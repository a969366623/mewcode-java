package com.mewcode.remote;

import java.time.Clock;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.HashMap;
import java.util.Map;

/** Server-side limits for an untrusted public demo. */
final class DemoUsageGuard {

    private static final ZoneId RESET_ZONE = ZoneId.of("Asia/Shanghai");
    private static final double TOKEN_ESTIMATE_SAFETY_FACTOR = 1.25;

    private final boolean enabled;
    private final int dailyTokenBudget;
    private final int globalDailyRequestLimit;
    private final int ipHourlyRequestLimit;
    private final int maxInputChars;
    private final int maxOutputTokens;
    private final int maxLlmCallsPerRequest;
    private final Clock clock;

    private final Map<String, HourlyCounter> hourlyCounters = new HashMap<>();
    private LocalDate currentDate;
    private int dailyRequests;
    private long reservedTokens;

    private DemoUsageGuard(boolean enabled, int dailyTokenBudget, int globalDailyRequestLimit,
                           int ipHourlyRequestLimit, int maxInputChars, int maxOutputTokens,
                           int maxLlmCallsPerRequest, Clock clock) {
        this.enabled = enabled;
        this.dailyTokenBudget = dailyTokenBudget;
        this.globalDailyRequestLimit = globalDailyRequestLimit;
        this.ipHourlyRequestLimit = ipHourlyRequestLimit;
        this.maxInputChars = maxInputChars;
        this.maxOutputTokens = maxOutputTokens;
        this.maxLlmCallsPerRequest = maxLlmCallsPerRequest;
        this.clock = clock;
        this.currentDate = LocalDate.now(clock.withZone(RESET_ZONE));
    }

    static DemoUsageGuard fromEnvironment() {
        return new DemoUsageGuard(
                booleanEnv("DEMO_MODE", false),
                intEnv("DEMO_DAILY_TOKEN_BUDGET", 100_000),
                intEnv("DEMO_GLOBAL_DAILY_REQUESTS", 20),
                intEnv("DEMO_IP_HOURLY_REQUESTS", 5),
                intEnv("DEMO_MAX_INPUT_CHARS", 2_000),
                intEnv("DEMO_MAX_OUTPUT_TOKENS", 1_500),
                intEnv("DEMO_MAX_LLM_CALLS_PER_REQUEST", 3),
                Clock.system(RESET_ZONE));
    }

    static DemoUsageGuard createForTest(int dailyTokenBudget, int globalDailyRequestLimit,
                                        int ipHourlyRequestLimit, int maxInputChars,
                                        Clock clock) {
        return new DemoUsageGuard(true, dailyTokenBudget, globalDailyRequestLimit,
                ipHourlyRequestLimit, maxInputChars, 1_500, 3, clock);
    }

    synchronized Decision allowRequest(String clientId, String content) {
        if (!enabled) return Decision.allow();
        resetDailyCountersIfNeeded();

        if (content.length() > maxInputChars) {
            return Decision.deny("输入过长，演示环境单次最多允许 " + maxInputChars + " 个字符。");
        }
        if (dailyRequests >= globalDailyRequestLimit) {
            return Decision.deny("今日演示次数已用完，请明天再试。");
        }

        long hour = clock.instant().getEpochSecond() / 3_600;
        HourlyCounter counter = hourlyCounters.get(clientId);
        if (counter == null || counter.hour() != hour) {
            counter = new HourlyCounter(hour, 0);
        }
        if (counter.count() >= ipHourlyRequestLimit) {
            return Decision.deny("你的每小时体验次数已用完，请稍后再试。");
        }

        hourlyCounters.put(clientId, new HourlyCounter(hour, counter.count() + 1));
        dailyRequests++;
        return Decision.allow();
    }

    synchronized boolean reserveLlmCall(int estimatedTokens) {
        if (!enabled) return true;
        resetDailyCountersIfNeeded();

        long conservativeEstimate = Math.max(1L,
                (long) Math.ceil(estimatedTokens * TOKEN_ESTIMATE_SAFETY_FACTOR));
        if (reservedTokens + conservativeEstimate > dailyTokenBudget) return false;
        reservedTokens += conservativeEstimate;
        return true;
    }

    boolean enabled() { return enabled; }
    int maxOutputTokens() { return maxOutputTokens; }
    int maxLlmCallsPerRequest() { return maxLlmCallsPerRequest; }

    private void resetDailyCountersIfNeeded() {
        LocalDate today = LocalDate.now(clock.withZone(RESET_ZONE));
        if (today.equals(currentDate)) return;
        currentDate = today;
        dailyRequests = 0;
        reservedTokens = 0;
        hourlyCounters.clear();
    }

    private static boolean booleanEnv(String name, boolean defaultValue) {
        String value = System.getenv(name);
        return value == null || value.isBlank() ? defaultValue : Boolean.parseBoolean(value);
    }

    private static int intEnv(String name, int defaultValue) {
        String value = System.getenv(name);
        if (value == null || value.isBlank()) return defaultValue;
        try {
            int parsed = Integer.parseInt(value);
            return parsed > 0 ? parsed : defaultValue;
        } catch (NumberFormatException ignored) {
            return defaultValue;
        }
    }

    record Decision(boolean allowed, String message) {
        static Decision allow() { return new Decision(true, ""); }
        static Decision deny(String message) { return new Decision(false, message); }
    }

    private record HourlyCounter(long hour, int count) {}
}
