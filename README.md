## 🔍 Checking Sessions in Redis

Redis sessions are stored in **DB1**, but the CLI connects to **DB0** by default.  
To inspect the session keys, run the following commands:

```bash
docker exec -it <your_redis_container_id> redis-cli
select 1
keys *
```

## 🛡️ API Documentation Viewing Permission

To allow a user to view the API documentation:

1. Open the **Django Admin Panel**.
2. Go to the **Users** section and select the desired user.
3. Scroll to the **Permissions** section (should be in box).
4. Enable the specific permission for viewing API documentation.

Once granted, the user will be able to access the docs interface.
![img.png](img.png)




