content = open('app/modules/users/router.py').read()
content = content.replace(
    '@router.delete("", status_code=204)\nasync def delete_account(user_id: CurrentUserId, db: DbSession) -> None:',
    '@router.delete("", status_code=200)\nasync def delete_account(user_id: CurrentUserId, db: DbSession) -> dict:'
)
content = content.replace(
    '    user.deleted_at = datetime.now(UTC)\n    await db.flush()',
    '    user.deleted_at = datetime.now(UTC)\n    await db.flush()\n    return {"message": "Account deleted"}'
)
open('app/modules/users/router.py', 'w').write(content)
print('Fix 1 done')