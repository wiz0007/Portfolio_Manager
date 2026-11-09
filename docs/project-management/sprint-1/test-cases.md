# Sprint 1 Test Cases

| ID | Test Case | Expected Result |
|---|---|---|
| TC-AUTH-01 | Register with valid email and password | 201 Created, returns user profile |
| TC-AUTH-02 | Register with already registered email | 400 Bad Request, email error message |
| TC-AUTH-03 | Login with valid credentials | 200 OK, session established |
| TC-AUTH-04 | Login with invalid password | 401 Unauthorized |
| TC-AUTH-05 | Access `/api/v1/auth/me/` without auth | 401/403 Forbidden |
| TC-AUTH-06 | Access `/api/v1/auth/me/` with valid session | 200 OK, returns user profile |
| TC-AUTH-07 | Logout | 200 OK, session invalidated |
