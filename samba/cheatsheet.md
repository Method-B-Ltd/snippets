List all fields of all users (will include computer accounts):
```bash
ldbsearch -H /var/lib/samba/private/sam.ldb '(objectclass=user)' '*'
```

List dn of all users (will include computer accounts):
```bash
ldbsearch -H /var/lib/samba/private/sam.ldb '(objectclass=user)' dn
```

List dn of all users (exclude computer accounts):
```bash
ldbsearch -H /var/lib/samba/private/sam.ldb '(&(objectClass=user)(!(objectClass=computer)))' dn
```

List dn of all *disabled* users (excluding computer accounts)
```bash
ldbsearch -H /var/lib/samba/private/sam.ldb '(&(objectClass=user)(!(objectClass=computer))(UserAccountControl:1.2.840.113556.1.4.803:=2))' dn
```

List dn of all *enabled* users (excluding computer accounts)
```bash
ldbsearch -H /var/lib/samba/private/sam.ldb '(&(objectClass=user)(!(objectClass=computer))(!(UserAccountControl:1.2.840.113556.1.4.803:=2)))' dn
```