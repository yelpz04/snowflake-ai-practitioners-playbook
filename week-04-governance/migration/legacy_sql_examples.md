# Migration Agent — Legacy SQL Examples

## Day 20: Snowflake Migration Agent

### Reference
- [Migration skill docs](https://docs.snowflake.com/en/migrations/migration-skill/skill)

### Sample Legacy SQL Scripts to Migrate

Use these as test inputs for the Snowflake Migration Agent.

---

### Script 1: Oracle-style PL/SQL
```sql
-- Oracle: Monthly sales summary procedure
CREATE OR REPLACE PROCEDURE monthly_sales_summary AS
  v_month DATE := TRUNC(SYSDATE, 'MM');
  v_count NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_count
  FROM sales_orders
  WHERE order_date >= v_month;

  DBMS_OUTPUT.PUT_LINE('Orders this month: ' || TO_CHAR(v_count));

  INSERT INTO monthly_summary (summary_date, order_count, created_at)
  VALUES (v_month, v_count, SYSDATE);

  COMMIT;
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('Error: ' || SQLERRM);
    ROLLBACK;
END;
/
```

### Script 2: SQL Server T-SQL
```sql
-- SQL Server: Customer health check with temp tables
CREATE PROCEDURE dbo.sp_customer_health_check
AS
BEGIN
    SET NOCOUNT ON;

    SELECT customer_id, customer_name,
           DATEDIFF(day, MAX(order_date), GETDATE()) AS days_since_last_order
    INTO #inactive_customers
    FROM customers c
    JOIN sales_orders o ON c.customer_id = o.customer_id
    GROUP BY c.customer_id, c.customer_name
    HAVING DATEDIFF(day, MAX(order_date), GETDATE()) > 180;

    SELECT ic.*, t.open_ticket_count
    FROM #inactive_customers ic
    LEFT JOIN (
        SELECT customer_id, COUNT(*) AS open_ticket_count
        FROM support_tickets
        WHERE status = 'Open'
        GROUP BY customer_id
    ) t ON ic.customer_id = t.customer_id;

    DROP TABLE #inactive_customers;
END;
GO
```

### Script 3: MySQL with specific syntax
```sql
-- MySQL: Auto-increment, backtick quoting, LIMIT
CREATE TABLE `daily_metrics` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `metric_date` DATE NOT NULL,
    `metric_name` VARCHAR(100),
    `metric_value` DECIMAL(10,2),
    `created_at` DATETIME DEFAULT NOW()
) ENGINE=InnoDB;

SELECT `metric_name`, AVG(`metric_value`) AS avg_val
FROM `daily_metrics`
WHERE `metric_date` >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
GROUP BY `metric_name`
ORDER BY avg_val DESC
LIMIT 10;
```

### Migration Workflow with Cortex Code

1. **Connect**: Point the Migration Agent at source database (or provide scripts)
2. **Assess**: "Assess these SQL scripts for Snowflake compatibility"
3. **Convert**: "Convert these to Snowflake SQL"
4. **Deploy**: "Deploy the converted scripts to REVENUE_OPS_AI.ANALYTICS"
5. **Validate**: "Validate the migration — check row counts and data types"

### LinkedIn Post Angle
"I gave the Snowflake Migration Agent 3 legacy SQL scripts (Oracle, SQL Server, MySQL). In minutes, it assessed compatibility, converted the syntax, and deployed to Snowflake. No manual rewrite."
