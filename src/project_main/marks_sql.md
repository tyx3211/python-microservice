在 MySQL 中，`UPDATE` 语句中的 `WHERE id IN (...)` 语法要求子查询返回的必须是与外部查询的 `id` 字段类型匹配的结果集，通常是 `id` 列。不能在 `IN` 子查询中直接使用其他字段，因为 `IN` 关键字只接受一个列作为参数进行匹配。

### 解释：

在这个查询中：

```sql
UPDATE employees
SET salary = salary * 1.10
WHERE id IN (
    SELECT e.id
    FROM employees e
    JOIN departments d ON e.department_id = d.id
    WHERE d.department_name = 'Sales'
);
```

子查询返回的是 `e.id`（`employees` 表中的 `id`）。外部查询中的 `WHERE id IN (...)` 会使用这个 `e.id` 来匹配要更新的记录。`id` 是被用作 **条件** 来确定哪些记录需要更新。

### 为什么 `IN` 中不能使用其他字段？

`IN` 子查询的逻辑是将 **子查询返回的一列值** 和外部查询的 `WHERE` 条件中的 `id` 进行匹配。如果你尝试在子查询中使用其他字段，MySQL 不会知道如何与外部的 `id` 字段进行匹配。

比如，下面的查询会导致错误：

```sql
UPDATE employees
SET salary = salary * 1.10
WHERE id IN (
    SELECT e.name  -- 错误：不能在 IN 子查询中使用非 id 字段
    FROM employees e
    JOIN departments d ON e.department_id = d.id
    WHERE d.department_name = 'Sales'
);
```

这会报错，因为 `IN` 子查询期望返回的结果应该是 `id` 列，而不是 `name` 列。

### 如果要根据其他字段来更新，可以使用 `JOIN` 语法

如果你希望基于 `name` 或其他字段进行条件判断，可以考虑使用 `JOIN` 来代替 `IN`，比如：

```sql
UPDATE employees e
JOIN departments d ON e.department_id = d.id
SET e.salary = e.salary * 1.10
WHERE d.department_name = 'Sales';
```

在这种情况下，`JOIN` 会将 `employees` 和 `departments` 表进行连接，然后根据 `department_name = 'Sales'` 的条件来更新 `salary`。这个查询比使用 `IN` 更清晰且性能更优，尤其在处理多个表的关联时。

### 总结

1. **不能在 `IN` 子查询中使用非匹配字段**：`IN` 子查询要求返回一个列（通常是 `id` 字段），该列与外部查询中的 `WHERE` 条件相匹配。
2. **使用 `JOIN` 替代 `IN`**：如果你需要根据其他字段来执行更新操作，使用 `JOIN` 更加直观和高效。
   
如果你有更多具体需求或更复杂的场景，可以告诉我，我可以帮助你构建相应的查询。