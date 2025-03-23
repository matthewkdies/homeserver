#!/bin/sh

# -----------------------------------------------------------------
# This is a custom entrypoint file to set any environment variables
# from secret files. This is the most secure way to set any 
# variables that may be necessary in the container's configuration 
# files) but don't want set on the host/defined in a compose file.
# -----------------------------------------------------------------


echo "Setting environment variables from Docker secrets..."
# Iterate over all files in /run/secrets
for secret_file in /run/secrets/*; do
  # Ensure it's a regular file
  if [ -f "${secret_file}" ]; then
    echo "Secret file found at ${secret_file}."
    # Extract the filename and convert it to uppercase
    env_varname=$(basename "${secret_file}" | tr '[:lower:]' '[:upper:]')
    echo "Setting ${env_varname} variable."
    # Read the file's content and set it as an environment variable
    secret_value=$(cat "${secret_file}")
    export "${env_varname}=${secret_value}"
    echo "${env_varname} exported successfully."
  fi
done

echo "Setting POSTGRES_CONNECTION variable."
export POSTGRES_CONNECTION="Host=lubelogger-postgres:5432;Username=${POSTGRES_USER};Password=${POSTGRES_PASSWORD};Database=lubelogger"
echo "POSTGRES_CONNECTION exported successfully."

# execute the command passed to the script
echo "Executing entrypoint: $*."
exec "$@"
