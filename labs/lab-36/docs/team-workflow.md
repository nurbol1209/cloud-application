# Коллективная работа с репозиторием

## Удалённый репозиторий

```bash
git remote add origin https://github.com/<пользователь>/<репозиторий>.git
git push -u origin main
```

## Клонирование

```bash
git clone https://github.com/<пользователь>/<репозиторий>.git
cd <репозиторий>
git status
```

## Получение изменений

```bash
git switch main
git pull origin main
```

## Рабочая ветвь

```bash
git switch -c feature/service-status-filter
git add app
git commit -m "TASK-02 Add service status filtering"
git push -u origin feature/service-status-filter
```

## Pull Request

1. Открыть репозиторий на GitHub.
2. Нажать **Compare & pull request** для отправленной ветви.
3. Описать изменение и связать его с TASK-02.
4. Получить проверку и выполнить **Merge pull request**.
5. Удалить ветвь на GitHub и локально:

```bash
git switch main
git pull origin main
git branch -d feature/service-status-filter
```

## Разрешение конфликта в README

При параллельном изменении одной строки в двух ветвях возникает конфликт.
Порядок действий:

```bash
git switch main
git pull origin main
git switch feature/service-status-filter
git merge main
# открыть README.md, выбрать итоговый текст,
# удалить маркеры <<<<<<< ======= >>>>>>>
git add README.md
git commit -m "Resolve README conflict"
git push
```

## Проверка результата

```bash
git log --oneline --graph --all
git status
```

## Вывод

Ветвление изолирует задачи; Pull Request фиксирует обсуждение и проверку;
регулярный `pull` уменьшает количество конфликтов.
