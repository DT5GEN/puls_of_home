# Промпт 1 для Claude Code: модель данных, переходы заявок, видимость, тесты

Скопируйте всё ниже разделителя в Claude Code как первое сообщение. В репозитории должны лежать `CLAUDE.md`, `docs/TZ_dom_status.md`, `docs/HISTORY.md` и `docs/dom_draft.json` (если последнего нет, выполните `python3 tools/gen_dom_draft.py`).

---

## Роль и контекст

Ты пишешь серверную часть домового портала. Это первый этап: только модель данных, бизнес-правила и тесты. Интерфейса, 3D, чатов и внешних интеграций в этом этапе нет.

Перед началом прочитай `CLAUDE.md`, `docs/TZ_dom_status.md` (полное ТЗ), `docs/HISTORY.md` (история решений) и `docs/dom_draft.json` (схема дома). Если что-то в этих файлах противоречит этому промпту, приоритет у этого промпта, а противоречие запиши в `OPEN_QUESTIONS.md`.

## Что строим в этом этапе

1. Загрузка и валидация `dom_draft.json`.
2. Схема базы данных PostgreSQL.
3. Сид-скрипт, который переносит JSON в базу.
4. Модуль переходов состояний заявки.
5. Модуль видимости полей заявки для разных ролей.
6. Ограничение числа мест в квартире.
7. Журнал событий заявки.
8. Функция эскалации аварий с подменяемым временем.
9. Тесты на всё перечисленное.

## Что НЕ делаем

- Интерфейс любого вида (ни React, ни HTML).
- 3D-модель и Three.js.
- Чаты, WebSocket, SSE.
- Вход, регистрацию, токены. Для тестов используй фиктивные идентификаторы мест и ролей, передаваемые в функции явно.
- Внешние API, отправку email и SMS, уведомления.
- Поля для персональных данных: ФИО, email, телефон, адрес проживания, паспорт, фото лица. Если видишь такое поле где-либо, не добавляй его.
- Новые категории обращений, типы объектов, роли или статусы сверх описанных здесь.
- Изменения структуры `dom_draft.json` без записи в `OPEN_QUESTIONS.md`.

Если что-то не описано в этом промпте и не решается очевидным образом, не выдумывай поведение. Выбери значение по умолчанию из раздела «Значения по умолчанию» или запиши вопрос в `OPEN_QUESTIONS.md` и продолжай с безопасным вариантом.

## Технический стек (фиксированный)

- Node.js LTS, TypeScript в строгом режиме (`strict: true`).
- Fastify не нужен на этом этапе. Только библиотека и тесты, без HTTP-сервера.
- PostgreSQL 16 в Docker через `docker-compose.yml`.
- Prisma для схемы и миграций.
- Zod для валидации JSON.
- Vitest для тестов.
- Все зависимости фиксируй через lock-файл.

Структура репозитория:

```
/prisma/schema.prisma
/prisma/migrations/
/src/domain/
    transitions.ts        переходы состояний заявки
    visibility.ts         правила видимости полей
    seats.ts              лимит мест в квартире
    escalation.ts         эскалация аварий
    events.ts             журнал событий
    types.ts              общие типы и перечисления
/src/schema/
    dom.zod.ts            Zod-схема для dom_draft.json
/src/seed/
    seed.ts               перенос JSON в базу
/tests/
    transitions.test.ts
    visibility.test.ts
    seats.test.ts
    escalation.test.ts
    seed.test.ts
    events.test.ts
docker-compose.yml
README.md
OPEN_QUESTIONS.md
```

## Модель данных

Все первичные ключи — uuid (`@default(uuid())`). Поле `kod` хранится отдельно и уникально. Связи только через uuid.

Таблицы и обязательные поля:

**Locality** (населённый пункт): `id`, `index` (строка из 6 цифр), `code` (короткий код, уникален в пределах индекса), `name`.

**Street**: `id`, `localityId` (FK), `slug` (уникален в пределах localityId), `name`.

**Building** (дом): `id`, `streetId` (FK), `number` (строка), `kod` (уникален), `floors` (целое), `apartmentsTotal` (по данным, по умолчанию 209), `apartmentsModel` (фактическое число созданных квартир), уникальность (`streetId`, `number`).

**BuildingGroup** (группа домов): `id`, `kod` (уникален), `name`. Связь «многие ко многим» с Building через таблицу `BuildingGroupMember`.

**Section** (секция): `id`, `buildingId` (FK), `number` (целое), `kod` (уникален), `apartmentsPerFloor` (целое). Уникальность (`buildingId`, `number`).

**CommonZone** (общая зона секции): `id`, `sectionId` (FK), `type` (enum из JSON: `vkhodnaya_gruppa`, `tambur`, `lift`, `lestnica`, `okna_v_podezde`, `dveri_v_podezde`), `kod` (уникален).

**Floor**: `id`, `sectionId` (FK), `number`, `kod` (уникален). Уникальность (`sectionId`, `number`).

**Apartment**: `id`, `floorId` (FK), `number` (целое, сквозной в доме), `kod` (уникален), `isActive` (булево, по умолчанию true), `seatLimit` (целое, по умолчанию 2). Уникальность (`buildingId`, `number`), buildingId получается через floor → section → building; для этого добавь денормализованное поле `buildingId` с проверкой на уровне сервиса или триггера.

**Window**: `id`, `apartmentId` (FK), `side` (строка, например `fasad`), `isPlaceholder` (булево), `kod` (уникален).

**CommonObject** (территория и групповые объекты): `id`, `kod` (уникален), `type` (enum из JSON для двора: `parkovka`, `vezdnaya_gruppa`, `podval`, `detskie_ploshchadki`, `ulichnoe_osveshchenie`, `zona_avtopoliva`, `besedka`, `urny`, `lavochki`, `gazony`, `bombouboezhishche`), `scopeType` (`building` или `group`), `scopeId`. Для групповых объектов есть связь с домами через `CommonObjectBuilding` (поле `obsluzhivaet` из JSON).

**Seat** (место в квартире): `id`, `apartmentId` (FK), `pseudonym` (строка до 40 символов), `status` (`active` или `revoked`), `createdAt`, `revokedAt`. Персональных данных нет.

**Request** (обращение): `id`, `apartmentId` (FK), `authorSeatId` (FK на Seat), `kind` (`request`, `complaint`, `suggestion`), `placeScope` (`apartment`, `section_common`, `building_common`, `yard`), `claimedDoneAt` (nullable), `actualDoneAt` (nullable), `category` (enum из раздела «Категории»), `state` (enum из раздела «Состояния»), `visibilityMode` (`public`, `color_only`, `restricted`), `description` (строка до 2000 символов), `createdAt`, `updatedAt`, `escalatedAt` (nullable), `closedAt` (nullable).

**RequestConfirmation** (подтверждение закрытия): `id`, `requestId` (FK), `role` (`author` или `verifier`), `seatId` (FK), `confirmedAt`. Уникальность (`requestId`, `role`).

**ModeratorAssignment**: `id`, `sectionId` (FK), `seatId` (FK), `assignedAt`, `revokedAt`. Одновременно у секции может быть активен не более одного модератора; проверь это индексом с условием или сервисной проверкой и тестом.

**RequestEvent** (журнал, только добавление): `id`, `requestId` (FK), `actorType` (`seat`, `system`, `uk`), `actorId` (nullable), `type` (строка), `fromState` (nullable), `toState` (nullable), `payload` (JSON, без персональных данных), `createdAt`. Запрещены UPDATE и DELETE по этой таблице. Добавь тест, который проверяет это на уровне репозитория.

**ColorState** (вычисляемый цвет окна): не хранится в базе, вычисляется функцией из открытых заявок квартиры (см. ниже).

## Категории обращений

Используй ровно такой список, в виде enum: `electricity`, `plumbing`, `elevator`, `landscaping`, `cleanliness`, `roof`, `doors_locks`, `yard`, `other`. Русские подписи храни отдельным словарём в `src/domain/types.ts`. Список черновой, он записан в `OPEN_QUESTIONS.md` как вопрос к владельцу.

## Состояния заявки

Состояния: `created`, `accepted_by_uk`, `in_progress`, `done_by_uk`, `awaiting_confirmation`, `closed`. Дополнительно для аварий: `escalated` (это флаг `escalatedAt`, не отдельное состояние).

Разрешённые переходы (только они, всё остальное запрещено):

- `created` → `accepted_by_uk` (актор: представитель УК)
- `accepted_by_uk` → `in_progress` (актор: представитель УК)
- `in_progress` → `done_by_uk` (актор: представитель УК)
- `done_by_uk` → `in_progress` (актор: представитель УК, допускается один раз, если работа не принята)
- `done_by_uk` → `awaiting_confirmation` (актор: система, автоматически)
- `awaiting_confirmation` → `closed` (актор: система, только при выполнении правила подтверждения для `placeScope`, см. раздел «Подтверждение закрытия»)

Переходов из `created` в `in_progress`, `done_by_uk` или `closed` нет. Переходов из `closed` никуда нет.

Для видов `suggestion` переходы другие: `created` → `accepted_by_uk` → `in_progress` → `done_by_uk` → `closed`. Подтверждение модератора здесь не требуется, достаточно подтверждения автора. Если не уверен, запиши в `OPEN_QUESTIONS.md`, но реализуй именно так.

Функция `canTransition(request, toState, actor)` возвращает `{ allowed: true }` или `{ allowed: false, reason: string }`. Причину пиши на русском в виде константы.

## Подтверждение закрытия

Переход в `closed` проверяется по `placeScope`:

- `apartment`: подтверждение роли `author` (житель этой квартиры). Модератор не участвует.
- `section_common` и `building_common`: серая отметка (`claimedDoneAt`) от УК или автора, затем подтверждение роли `verifier`, которым должен быть модератор другой секции этого дома. Если такого модератора в базе нет, допускается верифицированный житель другой секции.
- `yard`: как `section_common`.
- `suggestion` (`kind`): подтверждение роли `author`.

Ограничения, которые проверяются в `canTransition`: подтверждающий не может быть автором заявки; для `section_common` подтверждающий не может быть из той же секции; один seat даёт одно подтверждение на заявку.

Дата завершения: при подтверждении житель выбирает `claimedDoneAt` или `actualDoneAt`. Обе сохраняются. Статистика считается по `actualDoneAt`.

Проверка на сервере, в одной транзакции с записью события. Серая отметка не окрашивает окно в зелёный.

Для `kind: suggestion` правило про двух подтверждающих не действует, но переход в `closed` требует подтверждения автора. Это явно покрыто тестом.

## Видимость

Функция `visibleFields(request, viewer)` возвращает объект, в котором есть только разрешённые поля. Viewer описывается типом:

- `resident_same_apartment` — житель той же квартиры
- `resident_same_building` — житель другой квартиры того же дома
- `moderator_same_section` — модератор секции заявки
- `observer` — наблюдатель из другого дома группы (на этапе 1 всегда отключён)
- `uk` — представитель УК

Правила:

- `kind: request` + `category` аварийная (`electricity`, `plumbing` с признаком аварии): описание видно `resident_same_building` и выше. Модель аварии задаётся полем `isEmergency` в заявке, добавь его в таблицу. Поле `isEmergency` устанавливает только автор, понизить может только модератор (операция `downgrade_emergency`).
- `kind: complaint`: описание видно всем жильцам дома, если `visibilityMode = public`. Если `color_only` — описание видно только `resident_same_apartment` и `moderator_same_section`.
- `category: doors_locks`: описание только `resident_same_apartment` и `moderator_same_section`, цвет окна виден всем.
- `kind: suggestion`: описание видно всем жильцам дома; окно не окрашивается.
- `uk`: видит то же, что житель дома, плюс может менять состояние по правилам переходов.
- `observer`: если флаг наблюдателей выключен, функция возвращает пустой результат (тест на это).

Если окно окрашено, цвет вычисляется функцией `windowColor(apartment)`:
- есть открытая заявка `kind: request` с `isEmergency = true` → `red`
- есть открытая заявка `kind: complaint` или `request` без аварии → `yellow`
- иначе, если все заявки квартиры закрыты и подтверждены и `apartment.isActive = true` → `green`
- `apartment.isActive = false` → `grey`
- предложения (`suggestion`) на цвет не влияют.

Зелёный вычисляется автоматически и вручную не ставится (ТЗ, разделы 5а и 6).

## Лимит мест

Квартира может иметь не более `seatLimit` (по умолчанию 2) активных мест с `status = active`. Проверка в транзакции с блокировкой строки квартиры (`SELECT ... FOR UPDATE`) или через триггер. Тест на параллельное создание трёх мест: успешны только два.

Отозванное место (`revoked`) не учитывается.

## Эскалация аварий

Функция `escalate(now, config)` находит заявки с `isEmergency = true`, состояние не `closed` и не `done_by_uk`, у которых с `createdAt` или последнего события прошло больше `ESCALATION_HOURS` (по умолчанию 24). Для каждой такой заявки проставляет `escalatedAt` и пишет событие `escalated`.

Время передаётся аргументом, а не берётся из `new Date()` внутри функции. Тест использует фиктивное время.

## Сид

`seed.ts` читает `dom_draft.json`, валидирует через Zod, создаёт записи в правильном порядке (сначала локальность, улица, дом, группа, секции, этажи, квартиры, окна, общие зоны и объекты), генерирует uuid и сохраняет `kod`. Повторный запуск не создаёт дубликаты: используй upsert по `kod`.

Тест: после сида 210 квартир, 3 секции, 10 этажей в каждой, квартира 210 с `isActive = false`, 1 групповой объект с двумя домами.

## Значения по умолчанию

- `ESCALATION_HOURS = 24`
- `seatLimit = 2`
- `apartmentsTotal = 209`, `apartmentsModel` вычисляется из фактических квартир
- `visibilityMode = public` для `request` и `complaint`, кроме `doors_locks`, где `restricted`
- наблюдатели выключены

## Тесты, которые обязаны быть

1. Все разрешённые переходы проходят, все запрещённые возвращают `allowed: false` с причиной.
2. Переход в `closed` без требуемого подтверждения по `placeScope` запрещён. Отдельно проверь: `section_common` без проверки из другой секции не закрывается; `apartment` без подтверждения автора не закрывается; подтверждающий-автор не допускается.
3. Переход в `closed` для предложения требует только подтверждения автора.
4. Запись в `RequestEvent` нельзя обновить или удалить.
5. Видимость для каждого типа заявки и каждого viewer (хотя бы по одному случаю на комбинацию).
6. Наблюдатель при выключенном флаге не видит ничего.
7. Цвет окна для каждого из четырёх случаев.
8. Лимит мест: 2 успешно, 3-е отклоняется, включая параллельный тест.
9. Эскалация срабатывает после порога и не срабатывает до него, использует фиктивное время.
10. Сид идемпотентен: два запуска дают одинаковое число записей.
11. В схеме базы нет полей с именами вроде `fullName`, `email`, `phone`, `passport`. Тест читает `schema.prisma` и проверяет.

## Что вернуть в конце

1. `README.md`: как поднять базу (`docker compose up -d`), как применить миграции, как запустить сид и тесты.
2. `OPEN_QUESTIONS.md`: всё, что было неоднозначно.
3. Итоговый отчёт: сколько тестов прошло, какие переходы покрыты, какие пункты из списка выше не сделаны и почему.

Не переходи к интерфейсу и не добавляй функции сверх этого промпта, даже если кажется, что они нужны. Такие идеи запиши в `OPEN_QUESTIONS.md`.
