cd /opt/datacenter/Taipei-city-dashboard/

# 拉最新程式
git fetch origin sit
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse origin/sit)

if [ $LOCAL != $REMOTE ]; then
    echo "Changes detected. Pulling and restarting container..."
    git pull origin sit
    # docker compose restart
else
    echo "No changes."