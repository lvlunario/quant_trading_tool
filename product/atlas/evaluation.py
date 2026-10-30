"""Chronological split planning over session metadata, never prices or outcomes.

Session indices refer to a caller-defined ordered calendar. A label's end is
inclusive; touching a validation boundary therefore requires purging.
"""
from dataclasses import dataclass


def _session(value: int) -> bool:
    return type(value) is int and value >= 0


@dataclass(frozen=True)
class SampleWindow:
    decision_session: int
    feature_available_session: int
    label_end_session: int

    def __post_init__(self):
        if not all(_session(value) for value in (
                self.decision_session, self.feature_available_session,
                self.label_end_session)):
            raise ValueError('invalid_sample_session')
        if self.feature_available_session > self.decision_session:
            raise ValueError('future_feature')
        if self.label_end_session <= self.decision_session:
            raise ValueError('label_must_follow_decision')


@dataclass(frozen=True)
class FoldSpec:
    train_start: int
    validation_start: int
    validation_end: int  # exclusive
    holdout_start: int
    gap_sessions: int = 0

    def __post_init__(self):
        if not all(_session(value) for value in (
                self.train_start, self.validation_start, self.validation_end,
                self.holdout_start, self.gap_sessions)):
            raise ValueError('invalid_fold_session')
        if not (self.train_start < self.validation_start <
                self.validation_end <= self.holdout_start):
            raise ValueError('invalid_fold_order')
        if self.gap_sessions >= self.validation_start - self.train_start:
            raise ValueError('gap_removes_training_window')


@dataclass(frozen=True)
class FoldSplit:
    train_sessions: tuple[int, ...]
    validation_sessions: tuple[int, ...]
    purged_sessions: tuple[int, ...]
    excluded_sessions: tuple[int, ...]


def plan_fold(samples: tuple[SampleWindow, ...], spec: FoldSpec) -> FoldSplit:
    """Partition one sample per decision session; fail if either side is empty.

    Training labels must mature strictly before validation minus the safety
    gap. Validation labels must mature strictly before its exclusive end.
    Holdout samples and all other out-of-window samples remain excluded.
    This does not fit preprocessing or prove that supplied metadata is truthful.
    """
    if not isinstance(spec, FoldSpec) or not isinstance(samples, tuple):
        raise ValueError('invalid_split_input')
    if not samples or any(not isinstance(row, SampleWindow) for row in samples):
        raise ValueError('invalid_split_samples')
    decisions = tuple(row.decision_session for row in samples)
    if decisions != tuple(sorted(set(decisions))):
        raise ValueError('samples_must_be_unique_and_chronological')
    train, validation, purged, excluded = [], [], [], []
    for row in samples:
        decision = row.decision_session
        if spec.train_start <= decision < spec.validation_start:
            target = (train if row.label_end_session <
                      spec.validation_start - spec.gap_sessions else purged)
        elif spec.validation_start <= decision < spec.validation_end:
            target = (validation if row.label_end_session <
                      spec.validation_end else purged)
        else:
            target = excluded
        target.append(decision)
    if not train or not validation:
        raise ValueError('insufficient_split_samples')
    return FoldSplit(tuple(train), tuple(validation), tuple(purged), tuple(excluded))
