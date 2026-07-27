#!/bin/bash

# Export PATH đặt lên đầu để cả tiến trình init và start đều nhận được Node
export PATH="${NVM_DIR}/versions/node/v${NODE_VERSION_DEVELOP}/bin/:${PATH}"

# Dùng đường dẫn tương đối (vì lúc này đang đứng ở /workspace)
if [ -d "frappe-bench/apps/frappe" ]; then
    echo "Bench already exists, skipping init"
    cd frappe-bench
else
    echo "Creating new bench in workspace..."
    bench init --skip-redis-config-generation frappe-bench
    
    cd frappe-bench

    # Cấu hình các dịch vụ
    bench set-mariadb-host mariadb
    bench set-redis-cache-host redis://redis:6379
    bench set-redis-queue-host redis://redis:6379
    bench set-redis-socketio-host redis://redis:6379

    # CHỈ xóa redis khỏi Procfile, GIỮ LẠI watch để tự cập nhật frontend
    sed -i '/redis/d' ./Procfile

    # Quá trình này sẽ tải code về thư mục máy thật của bạn
    bench get-app payments
    bench get-app lms

    bench new-site lms.localhost \
    --force \
    --mariadb-root-password 123 \
    --admin-password admin \
    --no-mariadb-socket

    bench --site lms.localhost install-app payments
    bench --site lms.localhost install-app lms
    
    # Bật developer_mode để tự cập nhật Backend (Python)
    bench --site lms.localhost set-config developer_mode 1
    bench --site lms.localhost clear-cache
    bench use lms.localhost
fi

# Dù là bench cũ hay mới, cuối cùng đều chạy lệnh start
bench start