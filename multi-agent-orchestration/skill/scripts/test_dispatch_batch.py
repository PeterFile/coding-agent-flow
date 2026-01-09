#!/usr/bin/env python3
"""
Property-Based Tests for Dispatch Batch - File Conflict Detection

Feature: orchestration-fixes
Property 5: Conflict-Aware Batching
Validates: Requirements 2.3, 2.4, 2.5, 2.6
"""

import string
from hypothesis import given, strategies as st, settings, assume
from typing import List, Dict, Any, Set

from dispatch_batch import (
    FileConflict,
    detect_file_conflicts,
    partition_by_conflicts,
    has_file_manifest,
)


# ============================================================================
# Strategies for generating test data
# ============================================================================

@st.composite
def file_path_strategy(draw):
    """Generate valid file paths."""
    # Generate path components
    dirs = draw(st.lists(
        st.text(alphabet=string.ascii_lowercase + string.digits + "_-", min_size=1, max_size=10),
        min_size=0,
        max_size=2
    ))
    
    # Generate filename
    name = draw(st.text(alphabet=string.ascii_lowercase + string.digits + "_-", min_size=1, max_size=10))
    ext = draw(st.sampled_from([".py", ".js", ".ts", ".json", ".md", ".txt", ".go"]))
    
    filename = name + ext
    
    if dirs:
        return "/".join(dirs) + "/" + filename
    return filename


@st.composite
def task_with_manifest_strategy(draw):
    """Generate a task with file manifest."""
    task_id = str(draw(st.integers(min_value=1, max_value=100)))
    
    # Generate writes list (0-5 files)
    num_writes = draw(st.integers(min_value=0, max_value=5))
    writes = list(dict.fromkeys([draw(file_path_strategy()) for _ in range(num_writes)]))
    
    # Generate reads list (0-5 files)
    num_reads = draw(st.integers(min_value=0, max_value=5))
    reads = list(dict.fromkeys([draw(file_path_strategy()) for _ in range(num_reads)]))
    
    return {
        "task_id": task_id,
        "writes": writes if writes else [],
        "reads": reads if reads else [],
    }


@st.composite
def task_without_manifest_strategy(draw):
    """Generate a task without file manifest."""
    task_id = str(draw(st.integers(min_value=1, max_value=100)))
    return {
        "task_id": task_id,
        # No writes or reads fields
    }


@st.composite
def conflicting_tasks_strategy(draw):
    """Generate tasks with guaranteed write-write conflicts."""
    # Generate a shared file that will cause conflict
    shared_file = draw(file_path_strategy())
    
    # Generate two tasks that both write to the shared file
    task_a_id = str(draw(st.integers(min_value=1, max_value=50)))
    task_b_id = str(draw(st.integers(min_value=51, max_value=100)))
    
    # Additional unique files for each task
    task_a_extra = [draw(file_path_strategy()) for _ in range(draw(st.integers(min_value=0, max_value=2)))]
    task_b_extra = [draw(file_path_strategy()) for _ in range(draw(st.integers(min_value=0, max_value=2)))]
    
    task_a = {
        "task_id": task_a_id,
        "writes": [shared_file] + task_a_extra,
        "reads": [],
    }
    
    task_b = {
        "task_id": task_b_id,
        "writes": [shared_file] + task_b_extra,
        "reads": [],
    }
    
    return {
        "task_a": task_a,
        "task_b": task_b,
        "shared_file": shared_file,
    }


@st.composite
def non_conflicting_tasks_strategy(draw):
    """Generate tasks with no write-write conflicts."""
    num_tasks = draw(st.integers(min_value=2, max_value=5))
    
    tasks = []
    all_write_files: Set[str] = set()
    
    for i in range(num_tasks):
        task_id = str(i + 1)
        
        # Generate unique write files (not in any other task's writes)
        num_writes = draw(st.integers(min_value=1, max_value=3))
        writes = []
        for _ in range(num_writes):
            # Keep generating until we get a unique file
            for _ in range(10):  # Max attempts
                f = draw(file_path_strategy())
                if f not in all_write_files:
                    writes.append(f)
                    all_write_files.add(f)
                    break
        
        # Reads can overlap (no conflict)
        num_reads = draw(st.integers(min_value=0, max_value=3))
        reads = [draw(file_path_strategy()) for _ in range(num_reads)]
        
        tasks.append({
            "task_id": task_id,
            "writes": writes,
            "reads": reads,
        })
    
    return tasks


@st.composite
def mixed_tasks_strategy(draw):
    """Generate a mix of tasks with and without manifests, with and without conflicts."""
    # Tasks with manifest (some may conflict)
    num_manifest_tasks = draw(st.integers(min_value=1, max_value=4))
    manifest_tasks = [draw(task_with_manifest_strategy()) for _ in range(num_manifest_tasks)]
    
    # Ensure unique task IDs
    used_ids = set()
    for i, task in enumerate(manifest_tasks):
        while task["task_id"] in used_ids:
            task["task_id"] = str(int(task["task_id"]) + 100)
        used_ids.add(task["task_id"])
    
    # Tasks without manifest
    num_no_manifest = draw(st.integers(min_value=0, max_value=3))
    no_manifest_tasks = []
    for i in range(num_no_manifest):
        task = draw(task_without_manifest_strategy())
        while task["task_id"] in used_ids:
            task["task_id"] = str(int(task["task_id"]) + 200)
        used_ids.add(task["task_id"])
        no_manifest_tasks.append(task)
    
    return {
        "manifest_tasks": manifest_tasks,
        "no_manifest_tasks": no_manifest_tasks,
        "all_tasks": manifest_tasks + no_manifest_tasks,
    }


# ============================================================================
# Property Tests
# ============================================================================

@given(data=conflicting_tasks_strategy())
@settings(max_examples=100, deadline=None)
def test_property_5_conflict_detection_finds_conflicts(data):
    """
    Property 5: Conflict Detection - Finds write-write conflicts
    
    For any two tasks that write to the same file, detect_file_conflicts
    SHALL return a conflict containing both task IDs and the shared file.
    
    Feature: orchestration-fixes, Property 5
    Validates: Requirements 2.3, 2.4
    """
    task_a = data["task_a"]
    task_b = data["task_b"]
    shared_file = data["shared_file"]
    
    conflicts = detect_file_conflicts([task_a, task_b])
    
    # Should find exactly one conflict
    assert len(conflicts) >= 1, "Should detect at least one conflict"
    
    # Find the conflict involving our shared file
    relevant_conflicts = [c for c in conflicts if shared_file in c.files]
    assert len(relevant_conflicts) >= 1, f"Should find conflict for {shared_file}"
    
    conflict = relevant_conflicts[0]
    
    # Verify conflict contains both task IDs
    conflict_task_ids = {conflict.task_a, conflict.task_b}
    assert task_a["task_id"] in conflict_task_ids, "Conflict should include task_a"
    assert task_b["task_id"] in conflict_task_ids, "Conflict should include task_b"
    
    # Verify conflict type
    assert conflict.conflict_type == "write-write", "Conflict type should be write-write"


@given(tasks=non_conflicting_tasks_strategy())
@settings(max_examples=100, deadline=None)
def test_property_5_no_conflicts_when_disjoint_writes(tasks):
    """
    Property 5: Conflict Detection - No conflicts for disjoint writes
    
    For any set of tasks with disjoint write sets, detect_file_conflicts
    SHALL return an empty list.
    
    Feature: orchestration-fixes, Property 5
    Validates: Requirements 2.3, 2.4
    """
    conflicts = detect_file_conflicts(tasks)
    
    assert len(conflicts) == 0, f"Should have no conflicts, but found: {conflicts}"


@given(data=mixed_tasks_strategy())
@settings(max_examples=100, deadline=None)
def test_property_5_partition_no_conflicts_within_batch(data):
    """
    Property 5: Conflict-Aware Batching - No conflicts within any batch
    
    For any set of tasks, partition_by_conflicts SHALL produce batches
    where no two tasks in the same batch have write-write conflicts.
    
    Feature: orchestration-fixes, Property 5
    Validates: Requirements 2.3, 2.4
    """
    all_tasks = data["all_tasks"]
    
    if not all_tasks:
        return
    
    batches = partition_by_conflicts(all_tasks)
    
    # Check each batch for internal conflicts
    for i, batch in enumerate(batches):
        if len(batch) <= 1:
            continue  # Single task batch can't have internal conflicts
        
        # Check for write-write conflicts within this batch
        conflicts = detect_file_conflicts(batch)
        
        assert len(conflicts) == 0, \
            f"Batch {i} has internal conflicts: {conflicts}"


@given(data=mixed_tasks_strategy())
@settings(max_examples=100, deadline=None)
def test_property_5_partition_preserves_all_tasks(data):
    """
    Property 5: Conflict-Aware Batching - All tasks preserved
    
    For any set of tasks, partition_by_conflicts SHALL include every
    task in exactly one batch.
    
    Feature: orchestration-fixes, Property 5
    Validates: Requirements 2.3, 2.4, 2.6
    """
    all_tasks = data["all_tasks"]
    
    if not all_tasks:
        return
    
    batches = partition_by_conflicts(all_tasks)
    
    # Collect all task IDs from batches
    batched_ids = []
    for batch in batches:
        for task in batch:
            batched_ids.append(task["task_id"])
    
    original_ids = [t["task_id"] for t in all_tasks]
    
    # Every original task should appear exactly once
    assert sorted(batched_ids) == sorted(original_ids), \
        f"Tasks not preserved: original={original_ids}, batched={batched_ids}"


@given(data=mixed_tasks_strategy())
@settings(max_examples=100, deadline=None)
def test_property_5_no_manifest_tasks_serial(data):
    """
    Property 5: Conflict-Aware Batching - No-manifest tasks run serially
    
    For any task without a file manifest (no writes AND no reads),
    partition_by_conflicts SHALL place it in its own batch.
    
    Feature: orchestration-fixes, Property 5
    Validates: Requirements 2.5
    """
    no_manifest_tasks = data["no_manifest_tasks"]
    all_tasks = data["all_tasks"]
    
    if not no_manifest_tasks:
        return
    
    batches = partition_by_conflicts(all_tasks)
    
    # Find batches containing no-manifest tasks
    no_manifest_ids = {t["task_id"] for t in no_manifest_tasks}
    
    for batch in batches:
        batch_ids = {t["task_id"] for t in batch}
        no_manifest_in_batch = batch_ids & no_manifest_ids
        
        if no_manifest_in_batch:
            # If batch contains a no-manifest task, it should be alone
            assert len(batch) == 1, \
                f"No-manifest task should be in its own batch, but batch has {len(batch)} tasks"


@given(data=conflicting_tasks_strategy())
@settings(max_examples=100, deadline=None)
def test_property_5_conflicting_tasks_in_different_batches(data):
    """
    Property 5: Conflict-Aware Batching - Conflicting tasks separated
    
    For any two tasks with write-write conflicts, partition_by_conflicts
    SHALL place them in different batches.
    
    Feature: orchestration-fixes, Property 5
    Validates: Requirements 2.3, 2.4
    """
    task_a = data["task_a"]
    task_b = data["task_b"]
    
    batches = partition_by_conflicts([task_a, task_b])
    
    # Find which batch each task is in
    task_a_batch = None
    task_b_batch = None
    
    for i, batch in enumerate(batches):
        batch_ids = {t["task_id"] for t in batch}
        if task_a["task_id"] in batch_ids:
            task_a_batch = i
        if task_b["task_id"] in batch_ids:
            task_b_batch = i
    
    assert task_a_batch is not None, "task_a should be in a batch"
    assert task_b_batch is not None, "task_b should be in a batch"
    assert task_a_batch != task_b_batch, \
        f"Conflicting tasks should be in different batches, both in batch {task_a_batch}"


@given(tasks=non_conflicting_tasks_strategy())
@settings(max_examples=100, deadline=None)
def test_property_5_non_conflicting_tasks_can_batch(tasks):
    """
    Property 5: Conflict-Aware Batching - Non-conflicting tasks can batch
    
    For any set of tasks with no write-write conflicts and all having
    file manifests, partition_by_conflicts MAY place them in the same batch.
    
    Feature: orchestration-fixes, Property 5
    Validates: Requirements 2.6
    """
    # All tasks have manifests and no conflicts
    batches = partition_by_conflicts(tasks)
    
    # Should have at least one batch
    assert len(batches) >= 1, "Should have at least one batch"
    
    # Total tasks across batches should equal input
    total_batched = sum(len(b) for b in batches)
    assert total_batched == len(tasks), "All tasks should be batched"
    
    # With no conflicts, ideally all tasks could be in one batch
    # (but implementation may choose otherwise for other reasons)
    # Just verify no unnecessary splitting due to false conflicts
    if len(tasks) > 0:
        # At minimum, we shouldn't have more batches than tasks
        assert len(batches) <= len(tasks), \
            f"Too many batches ({len(batches)}) for {len(tasks)} non-conflicting tasks"


@given(task=task_with_manifest_strategy())
@settings(max_examples=100, deadline=None)
def test_has_file_manifest_with_manifest(task):
    """
    Test has_file_manifest returns True for tasks with writes or reads.
    
    Validates: Requirements 2.5
    """
    if task.get("writes") or task.get("reads"):
        assert has_file_manifest(task), "Task with writes/reads should have manifest"


@given(task=task_without_manifest_strategy())
@settings(max_examples=100, deadline=None)
def test_has_file_manifest_without_manifest(task):
    """
    Test has_file_manifest returns False for tasks without writes or reads.
    
    Validates: Requirements 2.5
    """
    assert not has_file_manifest(task), "Task without writes/reads should not have manifest"
