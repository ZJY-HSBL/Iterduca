from iterduca.services.restart_policy import CoreRestartPolicy


def test_restart_policy_limits_attempts_within_window() -> None:
    policy = CoreRestartPolicy(max_attempts=3, window_seconds=60)

    assert policy.allow(0.0) is True
    assert policy.allow(10.0) is True
    assert policy.allow(20.0) is True
    assert policy.allow(30.0) is False
    assert policy.remaining(30.0) == 0


def test_restart_policy_recovers_after_window_expires() -> None:
    policy = CoreRestartPolicy(max_attempts=2, window_seconds=60)

    assert policy.allow(0.0) is True
    assert policy.allow(1.0) is True
    assert policy.allow(10.0) is False
    assert policy.allow(61.0) is True
    assert policy.remaining(61.0) == 1
