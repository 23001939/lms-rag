#!/bin/bash
set -e  # Dừng script ngay lập tức nếu có lệnh bị lỗi

# Export PATH
export PATH="${NVM_DIR}/versions/node/v${NODE_VERSION_DEVELOP}/bin/:${PATH}"

# Chờ MariaDB sẵn sàng
echo "Waiting for MariaDB..."
while ! nc -z mariadb 3306; do
    sleep 2
done
echo "MariaDB is up and running."

# 1. Khởi tạo bench nếu chưa có
if [ ! -d "frappe-bench" ]; then
    echo "Creating new bench..."
    bench init --skip-redis-config-generation frappe-bench
    cd frappe-bench

    bench set-mariadb-host mariadb
    bench set-redis-cache-host redis://redis:6379
    bench set-redis-queue-host redis://redis:6379
    bench set-redis-socketio-host redis://redis:6379

    sed -i '/redis/d' ./Procfile

    # Lưu ý: Thay đổi URL git chính xác của team nếu là repo private
    bench get-app payments
    bench get-app lms

    echo "Installing AI dependencies for the first time..."
    bench pip install qdrant-client openai sentence-transformers langchain-text-splitters pypdf langchain-community unstructured python-docx python-pptx openpyxl
else
    echo "Bench folder already exists."
    cd frappe-bench
fi

# 2. Khởi tạo Site
if [ ! -d "sites/lms.localhost" ]; then
    echo "Site lms.localhost does not exist yet."

    if [ -f "../backup.sql" ]; then
        echo "Found backup.sql! Restoring database..."
        
        bench new-site lms.localhost \
            --force \
            --mariadb-root-password 123 \
            --admin-password admin \
            --no-mariadb-socket

        DB_NAME=$(python3 -c "import json; print(json.load(open('sites/lms.localhost/site_config.json'))['db_name'])" 2>/dev/null || echo "_d100d2879466358e")
        
        echo "Restoring database into $DB_NAME..."
        mysql -h mariadb -u root -p123 "$DB_NAME" < ../backup.sql
        
        bench --site lms.localhost migrate
    else
        echo "No backup.sql found. Creating fresh site..."
        
        bench new-site lms.localhost \
            --force \
            --mariadb-root-password 123 \
            --admin-password admin \
            --no-mariadb-socket

        bench --site lms.localhost install-app payments
        bench --site lms.localhost install-app lms
        bench --site lms.localhost install-app lms_ai
    fi
    
    bench --site lms.localhost set-config developer_mode 1
    bench --site lms.localhost clear-cache
else
    echo "Site lms.localhost already exists. Skipping site creation."
fi

bench use lms.localhost
bench start