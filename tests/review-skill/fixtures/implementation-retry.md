# 审查材料

要求：失败任务最多重试三次。

```ts
while (retryCount <= maxRetry) {
  await queue.enqueue(job);
  retryCount += 1;
}
```

测试只断言 `queue.enqueue` 被调用过。
