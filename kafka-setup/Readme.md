helm repo add kafka-ui https://provectus.github.io/kafka-ui-charts
helm upgrade --install kafka-ui kafka-ui/kafka-ui -f values.yml
