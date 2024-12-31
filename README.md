## Estella

A personal discord bot with utilities for my friends.

## Self-Hosting

**Note:** Self-hosting is not recommended. Use the official instance. If you still want to self-host, here’s how:

1. Clone the repository:
   ```bash
   git clone https://github.com/du-cki/Estella
   ```
2. Navigate to the project directory:
   ```bash
   cd Estella
   ```
3. Fill in the required environment variables in `docker-compose.yaml`.
4. Start the application:
   ```bash
   docker compose up -d
   ```

### Updating Your Instance

To update your self-hosted instance to the latest version:
```bash
git pull
docker compose up -d --build
```