# Additional Google Workspace Data Sources

## Summary

This document outlines additional Google Workspace configuration data that can be extracted using GAM beyond what's currently implemented.

## Currently Implemented ✅

| Data Type | GAM Command | Format | Status |
|-----------|-------------|--------|--------|
| Users | `gam print users formatjson` | JSON | ✅ Working |
| Groups | `gam print groups formatjson` | JSON | ✅ Working |
| Organizational Units | `gam print orgs` | CSV→JSON | ✅ Working |
| Calendar Resources | `gam print resources` | CSV→JSON | ✅ Working |
| Domain Settings | `gam info domain` | Text→JSON | ✅ Working |
| Security (2FA) | `gam print users fields 2FA` | JSON | ✅ Working |

## Discovered Additional Sources

### Priority 1: High Security Impact

#### 1. Mobile Devices 📱

**Status:** ✅ **3 devices found in your workspace**

**GAM Command:**
```bash
gam print mobile
```

**Data Captured:**
- Device ID and serial number
- Device type (iOS/Android)
- User assignment
- Approval status
- Security settings:
  - Encryption status
  - Password status
  - Compromised device detection
  - ADB status (Android Debug Bridge)
  - Unknown sources status
- Last sync time
- OS version and build

**Your Current Devices:**
- 2 iPhones (iOS 26.1)
- Status: APPROVED
- Encryption: ON
- No compromise detected

**Security Value:**
- BYOD (Bring Your Own Device) security monitoring
- Lost/stolen device tracking
- Compliance verification
- Remote wipe capability audit

**Implementation Difficulty:** Easy (CSV format, similar to OUs)

---

#### 2. Shared/Team Drives 🚗

**Status:** ✅ **1 shared drive found**

**GAM Command:**
```bash
gam print teamdrives
```

**Data Captured:**
- Drive ID and name
- Creation time
- Organizational unit
- Capabilities (what actions are allowed)
- Restrictions:
  - Domain users only
  - Copy requires writer permission
  - Download restrictions
  - Sharing restrictions
- Member management settings

**Security Value:**
- Data governance and DLP
- External sharing audit
- Permission drift detection
- Compliance monitoring

**Implementation Difficulty:** Easy (CSV format)

---

#### 3. OAuth Tokens 🔐

**Status:** ⚠️ High security concern

**GAM Command:**
```bash
gam print tokens
```

**Data Captured:**
- Application name
- Client ID
- Scopes granted
- User who authorized
- Authorization time
- Token status

**Security Value:** **CRITICAL**
- Third-party app access audit
- Over-privileged app detection
- Shadow IT discovery
- Data exfiltration risk assessment

**Implementation Difficulty:** Easy (CSV format)

---

#### 4. Admin Roles 👑

**GAM Command:**
```bash
gam print adminroles
```

**Data Captured:**
- Role ID and name
- Privileges granted
- Role assignments
- System vs custom roles
- Privilege scope

**Security Value:**
- Privileged access audit
- Least privilege enforcement
- Excessive permissions detection
- Compliance (who can do what)

**Implementation Difficulty:** Easy (CSV format)

---

### Priority 2: Operations & Management

#### 5. Chrome Devices 💻

**Status:** 0 devices found

**GAM Command:**
```bash
gam print cros
```

**Data Captured:**
- Device ID and serial
- Status and last sync
- Organizational unit
- User assignment
- OS version
- Auto-update settings

**Value:**
- ChromeOS fleet management
- Device compliance
- Update policy enforcement

**Implementation Difficulty:** Easy (CSV format)

---

#### 6. Licenses 🎫

**GAM Command:**
```bash
gam print licenses
```

**Data Captured:**
- SKU (product)
- User assignment
- License status
- Provisioned vs consumed

**Value:**
- Cost optimization
- License reclamation
- Compliance tracking

**Implementation Difficulty:** Easy (CSV format)

---

#### 7. Email Aliases 📧

**GAM Command:**
```bash
gam print aliases
```

**Data Captured:**
- Alias email
- Target (user/group)
- Target type

**Value:**
- Email routing audit
- Alias policy enforcement
- Shadow email detection

**Implementation Difficulty:** Easy (CSV format)

---

#### 8. App-Specific Passwords 🔑

**GAM Command:**
```bash
gam print asps
```

**Data Captured:**
- User
- ASP count
- Creation times

**Security Value:**
- Legacy auth method detection
- Security policy enforcement
- Migration to OAuth tracking

**Implementation Difficulty:** Easy

---

### Priority 3: Advanced/Optional

#### 9. Buildings 🏢

**GAM Command:**
```bash
gam print buildings
```

**Value:** Resource location management

---

#### 10. Custom Schemas 📋

**GAM Command:**
```bash
gam print schemas
```

**Value:** Custom organizational data

---

#### 11. Calendar Settings 📅

**GAM Command:**
```bash
gam user <email> print calendars
```

**Value:** Calendar permission audit

---

#### 12. Usage Reports 📊

**GAM Command:**
```bash
gam report users
```

**Value:** Activity tracking, license optimization

**Note:** Requires Reports API, different from regular GAM

---

## Security Analysis Opportunities

With these additional data sources, we can add new security rules:

### Mobile Device Security Rules

1. **Unencrypted Device Detection**
   - Severity: CRITICAL
   - Check: devices with encryption != ON

2. **Compromised Device Detection**
   - Severity: CRITICAL
   - Check: deviceCompromisedStatus != "Undetected"

3. **Outdated OS Detection**
   - Severity: MEDIUM
   - Check: OS version older than N releases

### OAuth Token Security Rules

1. **Over-Privileged App Detection**
   - Severity: HIGH
   - Check: Apps with excessive scopes (Drive, Gmail, etc.)

2. **Unknown Third-Party Apps**
   - Severity: MEDIUM
   - Check: Non-whitelisted applications

3. **Stale Token Detection**
   - Severity: LOW
   - Check: Tokens not used in 90+ days

### Shared Drive Security Rules

1. **External Sharing Enabled**
   - Severity: HIGH
   - Check: Domain users only = false

2. **Public Shared Drive**
   - Severity: CRITICAL
   - Check: Anyone with link can access

### Admin Role Security Rules

1. **Excessive Super Admins**
   - Severity: CRITICAL
   - Current: Already implemented
   - Enhancement: Also check custom admin role assignments

2. **Inactive Admin Accounts**
   - Severity: HIGH
   - Check: Admin roles on inactive users

## Recommended Implementation Order

### Phase 1: Critical Security (Immediate)
1. OAuth Tokens - Third-party app risk
2. Admin Roles - Privileged access audit
3. Mobile Devices - BYOD security

### Phase 2: Data Governance (Next)
4. Shared Drives - Data sharing audit
5. Aliases - Email routing control
6. App-Specific Passwords - Legacy auth

### Phase 3: Operations (Future)
7. Licenses - Cost optimization
8. Chrome Devices - Fleet management
9. Buildings - Resource management
10. Custom Schemas - Organizational data

## Estimated Implementation Time

- **Easy additions** (CSV format): 1-2 hours each
- **Security rules** for new data: 2-3 hours per data type
- **UI updates**: 1 hour (add to ConfigType enum and labels)

Total for Phase 1: ~8-10 hours

## Benefits

- **Security:** Comprehensive security posture visibility
- **Compliance:** Full audit trail of all workspace configurations
- **Cost:** License and resource optimization
- **Risk:** Third-party app and mobile device risk management
- **Governance:** Data sharing and access control monitoring

## Next Steps

1. Prioritize which data sources to add first
2. Implement extraction methods (similar to OU implementation)
3. Add corresponding security rules
4. Update UI to display new data types
5. Test with real data
6. Document new capabilities

