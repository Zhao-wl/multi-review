# 审查材料

要求：只有项目成员可以导出项目数据。

```ts
export async function exportProject(req: Request) {
  const user = requireAuthenticatedUser(req);
  const projectId = req.params.projectId;
  return exportService.export(projectId, user.id);
}
```

现有测试只验证未登录用户返回 401。
