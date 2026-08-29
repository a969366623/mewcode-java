FROM gradle:8.13-jdk21 AS build

WORKDIR /workspace
COPY . .
RUN gradle --no-daemon shadowJar

FROM eclipse-temurin:21-jre

WORKDIR /app
COPY --from=build /workspace/build/libs/mewcode.jar /app/mewcode.jar
COPY deploy/config.yaml /app/deploy/config.yaml

ENV JAVA_OPTS="-XX:MaxRAMPercentage=75.0"
EXPOSE 18888

CMD ["sh", "-c", "exec java $JAVA_OPTS -jar /app/mewcode.jar --remote=:${PORT:-18888} /app/deploy/config.yaml"]
