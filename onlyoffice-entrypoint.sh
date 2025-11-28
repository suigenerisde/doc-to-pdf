#!/bin/bash
# Custom entrypoint that starts OnlyOffice and the converter worker

# Update font cache if custom fonts exist
if [ -d /usr/share/fonts/truetype/custom-extra ] && [ "$(ls -A /usr/share/fonts/truetype/custom-extra 2>/dev/null)" ]; then
    echo "Updating font cache for custom fonts..."
    fc-cache -f -v /usr/share/fonts/truetype/custom-extra
fi

# Start the converter worker in background
(
    # Wait for x2t to be available
    while [ ! -f /var/www/onlyoffice/documentserver/server/FileConverter/bin/x2t ]; do
        sleep 5
    done

    echo "Starting converter worker..."
    mkdir -p /shared

    X2T_PATH="/var/www/onlyoffice/documentserver/server/FileConverter/bin/x2t"

    while true; do
        for marker in /shared/*.convert; do
            [ -e "$marker" ] || continue

            job_id=$(basename "$marker" .convert)
            config_file=$(cat "$marker")
            config_path="/shared/$config_file"

            echo "Processing job: $job_id"

            # Remove marker first to prevent reprocessing
            rm -f "$marker"

            if [ -f "$config_path" ]; then
                if "$X2T_PATH" "$config_path" 2>/tmp/x2t_error_$job_id.log; then
                    echo "Job $job_id completed successfully"
                    # Touch done file to signal completion
                    touch "/shared/$job_id.done"
                else
                    echo "Job $job_id failed"
                    cat /tmp/x2t_error_$job_id.log > "/shared/$job_id.error"
                    rm -f /tmp/x2t_error_$job_id.log
                fi
            else
                echo "Config file not found: $config_path"
                echo "Config file not found" > "/shared/$job_id.error"
            fi
        done
        sleep 0.3
    done
) &

# Start the main OnlyOffice Document Server
exec /app/ds/run-document-server.sh
