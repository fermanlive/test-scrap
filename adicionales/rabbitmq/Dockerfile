FROM rabbitmq:3-management

# Copiar configuración personalizada
COPY rabbitmq.conf /etc/rabbitmq/rabbitmq.conf
COPY enabled_plugins /etc/rabbitmq/enabled_plugins
COPY definitions.json /etc/rabbitmq/definitions.json

# Exponer puertos
EXPOSE 5672 15672

# Comando por defecto
CMD ["rabbitmq-server"]
