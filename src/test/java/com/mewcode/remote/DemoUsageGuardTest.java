package com.mewcode.remote;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.time.Clock;
import java.time.Instant;
import java.time.ZoneId;
import org.junit.jupiter.api.Test;

class DemoUsageGuardTest {

    @Test
    void enforcesInputRequestAndTokenLimits() {
        MutableClock clock = new MutableClock(Instant.parse("2026-08-30T00:00:00Z"));
        DemoUsageGuard guard = DemoUsageGuard.createForTest(100, 2, 1, 5, clock);

        assertFalse(guard.allowRequest("ip-a", "123456").allowed());
        assertTrue(guard.allowRequest("ip-a", "hello").allowed());
        assertFalse(guard.allowRequest("ip-a", "again").allowed());
        assertTrue(guard.allowRequest("ip-b", "hello").allowed());
        assertFalse(guard.allowRequest("ip-c", "hello").allowed());

        assertTrue(guard.reserveLlmCall(80));
        assertFalse(guard.reserveLlmCall(1));
    }

    @Test
    void resetsLimitsAtTheNextShanghaiDay() {
        MutableClock clock = new MutableClock(Instant.parse("2026-08-30T15:59:00Z"));
        DemoUsageGuard guard = DemoUsageGuard.createForTest(100, 1, 1, 5, clock);

        assertTrue(guard.allowRequest("ip-a", "hello").allowed());
        assertFalse(guard.allowRequest("ip-a", "again").allowed());

        clock.instant = Instant.parse("2026-08-30T16:01:00Z");
        assertTrue(guard.allowRequest("ip-a", "hello").allowed());
    }

    private static final class MutableClock extends Clock {
        private Instant instant;

        private MutableClock(Instant instant) {
            this.instant = instant;
        }

        @Override
        public ZoneId getZone() {
            return ZoneId.of("Asia/Shanghai");
        }

        @Override
        public Clock withZone(ZoneId zone) {
            return this;
        }

        @Override
        public Instant instant() {
            return instant;
        }
    }
}
