cd /opt/datacenter/Taipei-city-dashboard/

# 拉最新程式
git fetch origin develop
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse origin/develop)

if [ $LOCAL != $REMOTE ]; then
    echo "Changes detected. Pulling and restarting container..."
    git pull origin develop
    # docker compose restart
else
    echo "No changes."