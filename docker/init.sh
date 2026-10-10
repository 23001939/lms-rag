#!/bin/bash
set -e  # Dừng script ngay lập tức nếu có lệnh bị lỗi
set -o pipefail

# Export PATH
export PATH="${NVM_DIR}/versions/node/v${NODE_VERSION_DEVELOP}/bin/:${PATH}"

BENCH_DIR="/workspace/frappe-bench"
BACKUP_SQL="/workspace/backup.sql"

# Chờ MariaDB sẵn sàng
echo "Waiting for MariaDB..."
while ! timeout 3 bash -c 'echo > /dev/tcp/mariadb/3306' 2>/dev/null; do
    sleep 2
done
echo "MariaDB is up and running."

# 1. Khởi tạo bench nếu chưa có
if [ ! -d "$BENCH_DIR/apps/frappe" ]; then
    echo "Creating new bench at $BENCH_DIR..."
    cd /workspace
    bench init --skip-redis-config-generation frappe-bench
    cd "$BENCH_DIR"

    bench set-mariadb-host mariadb
    bench set-redis-cache-host redis://redis:6379
    bench set-redis-queue-host redis://redis:6379
    bench set-redis-socketio-host redis://redis:6379

    sed -i '/redis/d' ./Procfile

    # Lưu ý: Thay đổi URL git chính xác của team nếu là repo private
    bench get-app payments
    bench get-app lms
    bench get-app lms_ai

    echo "Installing AI dependencies for the first time..."
    bench pip install qdrant-client openai sentence-transformers langchain-text-splitters pypdf langchain-community unstructured python-docx python-pptx openpyxl
else
    echo "Bench folder already exists at $BENCH_DIR."
    cd "$BENCH_DIR"
fi

# Bench commands must run from the canonical bench root.
cd "$BENCH_DIR"

# 2. Khởi tạo Site
# config/pids is part of Bench's directory signature. Some bind-mounted
# workspaces lose this empty directory, which makes Bench hide Frappe commands.
mkdir -p config/pids

# A bind-mounted bench may not contain its ignored Python environment or its
# editable app installs. Check both because env can survive a failed startup.
if [ ! -x "env/bin/python" ]; then
    echo "Bench Python environment is missing. Recreating it..."
    bench setup env
fi

if ! ./env/bin/python -c 'import payments, lms, lms_ai' >/dev/null 2>&1; then
    echo "Installing the local Bench apps into the Python environment..."
    ./env/bin/python -m pip install -e ./apps/frappe
    ./env/bin/python -m pip install -e ./apps/lms
    ./env/bin/python -m pip install -e ./apps/payments
    ./env/bin/python -m pip install -e ./apps/lms_ai
fi

if ! ./env/bin/python -c 'import importlib.util, sys; sys.exit(any(importlib.util.find_spec(name) is None for name in ("qdrant_client", "openai", "sentence_transformers")))' >/dev/null 2>&1; then
    echo "AI Python dependencies are missing. Installing them..."
    ./env/bin/python -m pip install 'torch==2.14.1+cpu' --index-url https://download.pytorch.org/whl/cpu --extra-index-url https://pypi.org/simple
    ./env/bin/python -m pip install qdrant-client openai sentence-transformers langchain-text-splitters pypdf langchain-community unstructured python-docx python-pptx openpyxl
fi

# A bind-mounted bench can also lose its ignored Node dependency tree.
if ! (cd apps/frappe && node -e "require.resolve('socket.io')") >/dev/null 2>&1; then
    echo "Bench Node dependencies are missing. Installing them..."
    bench setup requirements --node
fi

if [ ! -d "sites/lms.localhost" ]; then
    echo "Site lms.localhost does not exist yet."

    if [ -f "$BACKUP_SQL" ]; then
        echo "Found backup.sql! Restoring database..."
        
        bench new-site lms.localhost \
            --force \
            --mariadb-root-password 123 \
            --admin-password admin \
            --no-mariadb-socket

        DB_NAME=$(python3 -c "import json; print(json.load(open('sites/lms.localhost/site_config.json'))['db_name'])" 2>/dev/null || echo "_d100d2879466358e")
        
        echo "Restoring database into $DB_NAME..."
        iconv -f UTF-16 -t UTF-8 "$BACKUP_SQL" | mysql --skip-ssl -h mariadb -u root -p123 "$DB_NAME"
        touch sites/lms.localhost/.restore_pending_migrate
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

# The site folder or an empty database can survive a failed restore. Check the
# core Frappe tables instead of only checking whether the schema exists.
if [ -d "sites/lms.localhost" ]; then
    DB_NAME=$(python3 -c "import json; print(json.load(open('sites/lms.localhost/site_config.json'))['db_name'])")
    CORE_TABLES=$(mysql --skip-ssl -h mariadb -u root -p123 -Nse "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='${DB_NAME}' AND table_name IN ('tabDocType','tabDefaultValue')")
    if [ "$CORE_TABLES" != "2" ]; then
        if [ -f "$BACKUP_SQL" ]; then
            echo "Database for lms.localhost is missing core tables. Restoring $BACKUP_SQL..."
            TEMP_BACKUP=$(mktemp /tmp/lms-backup.XXXXXX.sql)
            iconv -f UTF-16 -t UTF-8 "$BACKUP_SQL" > "$TEMP_BACKUP"
            CLIENT_WRAPPER_DIR=$(mktemp -d /tmp/mariadb-client.XXXXXX)
            REAL_MARIADB=$(command -v mariadb || command -v mysql)
            cat > "$CLIENT_WRAPPER_DIR/mariadb" <<'EOF'
#!/bin/sh
exec "$FRAPPE_REAL_MARIADB" --skip-ssl "$@"
EOF
            chmod +x "$CLIENT_WRAPPER_DIR/mariadb"
            if FRAPPE_REAL_MARIADB="$REAL_MARIADB" PATH="$CLIENT_WRAPPER_DIR:$PATH" bench --site lms.localhost restore "$TEMP_BACKUP" --db-root-password 123; then
                rm -rf "$CLIENT_WRAPPER_DIR" "$TEMP_BACKUP"
                touch sites/lms.localhost/.restore_pending_migrate
            else
                RESTORE_STATUS=$?
                rm -rf "$CLIENT_WRAPPER_DIR" "$TEMP_BACKUP"
                exit "$RESTORE_STATUS"
            fi
        else
            echo "Database for lms.localhost is missing and $BACKUP_SQL was not found." >&2
            exit 1
        fi
    fi
fi

if [ -f sites/lms.localhost/.restore_pending_migrate ]; then
    bench --site lms.localhost migrate
    rm -f sites/lms.localhost/.restore_pending_migrate
fi

bench use lms.localhost
bench start
