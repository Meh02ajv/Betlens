content = open('app/modules/odds_value/router.py').read()
content = content.replace(
    '@router.delete("/bets/{bet_id}", status_code=204)\nasync def delete_bet(bet_id: uuid.UUID, user_id: CurrentUserId, db: DbSession) -> None:',
    '@router.delete("/bets/{bet_id}", status_code=200)\nasync def delete_bet(bet_id: uuid.UUID, user_id: CurrentUserId, db: DbSession) -> dict:'
)
content = content.replace(
    '    await db.delete(bet)',
    '    await db.delete(bet)\n    return {"message": "Deleted"}'
)
open('app/modules/odds_value/router.py', 'w').write(content)
print('Fix 2 done')