# Ветви Git в проекте

## Схема

```
main
 ├── feature/status-validation   (TASK-01)
 │        ↓ merge --no-ff
 └── docs/status-description      (самостоятельное задание)
          ↓ merge --no-ff
```

## Просмотр ветвей

```bash
git branch
git branch -a
git log --oneline --graph --all
```

## Слияние

```bash
git switch main
git merge --no-ff feature/status-validation
```

Флаг `--no-ff` сохраняет отдельный коммит слияния, поэтому в истории видно,
что изменение выполнялось в отдельной ветви.

## Конфликты

Если обе ветви изменили один и тот же участок файла, Git сообщает о конфликте.
Конфликт разрешается вручную: выбрать итоговое содержимое, удалить маркеры
`<<<<<<<`, `=======`, `>>>>>>>`, затем выполнить `git add` и `git commit`.

## Удаление ветви

```bash
git branch -d feature/status-validation
```

Удаляется только указатель ветви. Коммиты, вошедшие в `main`, сохраняются.
