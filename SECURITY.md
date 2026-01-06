# Security Considerations

This document outlines security measures implemented in Market Atlas and recommendations for production deployment.

## Implemented Security Features

### Backend

1. **JWT Authentication**
   - Strong password requirements (8+ chars, uppercase, lowercase, digit)
   - JWT secret key validation (minimum 32 characters, no default values)
   - Access tokens expire after 30 minutes
   - Refresh token rotation (old tokens invalidated on use)

2. **Rate Limiting**
   - Registration: 5 attempts/hour per IP
   - Login: 10 attempts/minute per IP
   - Token refresh: 20 attempts/minute per IP

3. **Input Validation**
   - Stock ticker format validation
   - Email validation
   - Password strength enforcement
   - Pydantic schema validation on all inputs

4. **HTML/XSS Protection**
   - BeautifulSoup for safe HTML parsing (SEC filings)
   - No regex-based HTML stripping

5. **Database**
   - Async sessions with proper cleanup
   - SQL injection protection via SQLAlchemy ORM
   - Password hashing with bcrypt

6. **API Security**
   - CORS configuration
   - Request validation
   - Error handling without information leakage

### Frontend

1. **Authentication**
   - Token-based authentication
   - Automatic token refresh
   - Protected routes

## Production Recommendations

### Critical for Production

1. **Environment Variables**
   ```bash
   # Generate secure JWT secret (minimum 32 characters)
   openssl rand -hex 32

   # Set in .env file
   JWT_SECRET_KEY=<generated-secret>
   ```

2. **HTTPS Only**
   - Use HTTPS in production
   - Set `SECURE` flag on cookies
   - Enable HSTS (HTTP Strict Transport Security)

3. **Token Storage**
   - **Current**: Tokens stored in localStorage (vulnerable to XSS)
   - **Recommended**: Use httpOnly cookies for refresh tokens
   - **Implementation**:
     ```python
     # Backend: Set httpOnly cookie
     response.set_cookie(
         "refresh_token",
         value=refresh_token,
         httponly=True,
         secure=True,  # HTTPS only
         samesite="strict",
         max_age=7*24*60*60  # 7 days
     )
     ```

4. **Content Security Policy (CSP)**
   ```nginx
   # Add to nginx/web server config
   add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';";
   add_header X-Content-Type-Options "nosniff";
   add_header X-Frame-Options "DENY";
   add_header X-XSS-Protection "1; mode=block";
   ```

5. **Database Security**
   - Use strong database passwords
   - Limit database user permissions
   - Enable SSL for database connections
   - Regular backups with encryption

6. **API Keys**
   - Rotate API keys regularly
   - Use environment-specific keys
   - Monitor API usage for anomalies
   - Set up rate limiting at provider level

7. **Dependencies**
   ```bash
   # Regular security audits
   pip install safety
   safety check

   npm audit
   npm audit fix
   ```

8. **Logging & Monitoring**
   - Log authentication failures
   - Monitor for brute force attempts
   - Alert on suspicious activity
   - Don't log sensitive data (passwords, tokens)

### Additional Recommendations

1. **Two-Factor Authentication (2FA)**
   - Implement TOTP-based 2FA
   - Use libraries like `pyotp`

2. **Session Management**
   - Implement session timeout
   - Track active sessions
   - Allow users to revoke sessions

3. **API Rate Limiting**
   - Use Redis for distributed rate limiting
   - Implement per-user rate limits
   - Add exponential backoff

4. **Input Sanitization**
   - Validate file uploads
   - Sanitize user-generated content
   - Limit request size

5. **Error Handling**
   - Use generic error messages for users
   - Log detailed errors server-side
   - Don't expose stack traces

6. **Regular Security Audits**
   - Penetration testing
   - Code reviews focused on security
   - Update dependencies regularly
   - Subscribe to security advisories

## Testing Security

Run the test suite to verify security measures:

```bash
cd backend
pytest tests/ -v
```

Key test coverage:
- Password strength validation
- JWT secret validation
- Token rotation
- Input validation
- Authentication flows

## Incident Response

In case of a security incident:

1. **Immediate Actions**
   - Rotate all JWT secrets
   - Invalidate all tokens
   - Force password reset for affected users
   - Review access logs

2. **Investigation**
   - Identify breach vector
   - Assess scope of compromise
   - Document timeline

3. **Remediation**
   - Patch vulnerabilities
   - Update dependencies
   - Enhance monitoring
   - Notify affected users

## Contact

For security issues, please contact: [Your security contact]

**Do not** open public GitHub issues for security vulnerabilities.
