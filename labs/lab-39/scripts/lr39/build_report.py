"""Сборка отчёта ЛР 39: диаграммы PNG + DOCX."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

LAB = Path(__file__).resolve().parents[2]
DOCS = LAB / "docs"
DOCS.mkdir(exist_ok=True)

FONT_REG = r"C:\Windows\Fonts\arial.ttf"
FONT_BOLD = r"C:\Windows\Fonts\arialbd.ttf"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def center_text(draw, box, text, fnt, fill=(20, 20, 20)):
    x1, y1, x2, y2 = box
    lines = text.split("\n")
    heights = [draw.textbbox((0, 0), line, font=fnt)[3] for line in lines]
    total = sum(heights) + (len(lines) - 1) * 8
    y = y1 + (y2 - y1 - total) / 2
    for line, h in zip(lines, heights):
        w = draw.textbbox((0, 0), line, font=fnt)[2]
        draw.text((x1 + (x2 - x1 - w) / 2, y), line, font=fnt, fill=fill)
        y += h + 8


def box(draw, rect, text, fill, outline, radius=14, fnt=None):
    draw.rounded_rectangle(rect, radius=radius, fill=fill, outline=outline, width=3)
    center_text(draw, rect, text, fnt or font(22))


def arrow(draw, start, end, text="", fnt=None, fill=(70, 70, 70)):
    draw.line([start, end], fill=fill, width=4)
    x1, y1 = start
    x2, y2 = end
    dx, dy = x2 - x1, y2 - y1
    length = max((dx * dx + dy * dy) ** 0.5, 1)
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    tip = (x2, y2)
    left = (x2 - ux * 16 + px * 7, y2 - uy * 16 + py * 7)
    right = (x2 - ux * 16 - px * 7, y2 - uy * 16 - py * 7)
    draw.polygon([tip, left, right], fill=fill)
    if text:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        f = fnt or font(18)
        w = draw.textbbox((0, 0), text, font=f)[2]
        draw.rectangle([mx - w / 2 - 5, my - 15, mx + w / 2 + 5, my + 15], fill="white")
        draw.text((mx - w / 2, my - 12), text, font=f, fill=fill)


def build_network_diagram(path: Path):
    img = Image.new("RGB", (1700, 760), "white")
    d = ImageDraw.Draw(img)
    d.text((40, 24), "Рисунок 1. Сетевой путь к Cloud Application (ЛР 39)",
           font=font(26, True), fill=(10, 10, 10))

    # Внешний клиент и сетевой путь
    box(d, (40, 170, 330, 330),
        "Windows-клиент\nбраузер / curl /\nTest-NetConnection", "#DCE9F7", "#2F5597")
    box(d, (430, 160, 760, 340),
        "Сетевой интерфейс\n192.168.0.10/24\n(аналог Host-only)", "#E2F0D9", "#548235")
    box(d, (860, 160, 1160, 340),
        "Docker published port\n192.168.0.10:8080", "#FFF2CC", "#BF9000")
    box(d, (1260, 160, 1560, 340),
        "Контейнер app\n0.0.0.0:8000\nFastAPI / Uvicorn", "#DCE9F7", "#2F5597")

    arrow(d, (330, 250), (430, 250), "TCP/HTTP")
    arrow(d, (760, 250), (860, 250), "host bind")
    arrow(d, (1160, 250), (1260, 250), "forward")

    # Внутренняя сеть
    d.rounded_rectangle((900, 440, 1600, 720), radius=18, outline="#7F7F7F",
                        width=3, fill="#F7F7F7")
    d.text((925, 672), "cloud-network — внутренняя сеть Compose",
           font=font(18), fill=(90, 90, 90))
    box(d, (940, 520, 1230, 650), "db\npostgres:18\n172.18.0.3:5432", "#EDE7F6", "#5B3F98", fnt=font(20))
    box(d, (1290, 520, 1570, 650), "notification\n172.18.0.2:9000", "#EDE7F6", "#5B3F98", fnt=font(20))
    arrow(d, (1380, 340), (1150, 520), "HTTP", fnt=font(16))
    arrow(d, (1440, 340), (1430, 520), "HTTP", fnt=font(16))

    # Пояснения
    d.text((40, 400), "Внешняя публикация: только app", font=font(20, True), fill=(192, 0, 0))
    d.text((40, 440), "db:5432 и notification:9000\nнаружу не опубликованы", font=font(19), fill=(90, 90, 90))
    d.text((430, 400), "127.0.0.1:8080 недоступен\nсетевому клиенту", font=font(18), fill=(90, 90, 90))
    img.save(path, "PNG")


def build_diagnosis_diagram(path: Path):
    img = Image.new("RGB", (1250, 980), "white")
    d = ImageDraw.Draw(img)
    d.text((40, 24), "Рисунок 2. Последовательность диагностики сетевого доступа",
           font=font(25, True), fill=(10, 10, 10))

    items = [
        ("1. Клиент", "Test-NetConnection / curl\nадрес и TCP-порт"),
        ("2. Сетевой интерфейс", "ip -br addr / ip route\n(Windows: Get-NetIPAddress, Get-NetRoute)"),
        ("3. Прослушиваемый порт", "ss -ltn / Get-NetTCPConnection\nhost-адрес:порт"),
        ("4. Docker port mapping", "docker compose port app 8000"),
        ("5. Контейнер", "docker compose ps / logs"),
        ("6. Приложение изнутри", "docker compose exec ... /status"),
    ]
    y = 100
    for title, detail in items:
        d.rounded_rectangle((160, y, 1090, y + 110), radius=14, fill="#DCE9F7",
                            outline="#2F5597", width=3)
        d.text((185, y + 18), title, font=font(24, True), fill=(20, 40, 90))
        d.text((185, y + 55), detail, font=font(19), fill=(40, 40, 40))
        if y + 110 < 100 + 6 * 120:
            arrow(d, (625, y + 110), (625, y + 140))
        y += 140
    d.text((160, y + 10), "Отказ локализуется на первом уровне, где ожидаемый результат не совпал.",
           font=font(18), fill=(90, 90, 90))
    img.save(path, "PNG")


# ---------------------------------------------------------------------------
# DOCX helpers
# ---------------------------------------------------------------------------

def set_cell_bg(cell, color: str):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), color)
    tc_pr.append(shd)


def repeat_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    header = OxmlElement("w:tblHeader")
    header.set(qn("w:val"), "true")
    tr_pr.append(header)


def set_cell_text(cell, text: str, bold: bool = False, size: int = 10):
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(size)
    run.font.name = "Times New Roman"


def table(doc, headers, rows, widths=None, size=10):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t.rows[0]
    repeat_header(hdr)
    for cell, name in zip(hdr.cells, headers):
        set_cell_text(cell, name, bold=True, size=size)
        set_cell_bg(cell, "D9E2F3")
    for row in rows:
        cells = t.add_row().cells
        for cell, value in zip(cells, row):
            set_cell_text(cell, str(value), size=size)
    if widths:
        for row in t.rows:
            for cell, width in zip(row.cells, widths):
                cell.width = Cm(width)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def para(doc, text, bold=False, italic=False, size=12, align="justify", space_after=6,
         first_line=1.25):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    if align == "justify":
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    elif align == "center":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align == "left":
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    if first_line and align == "justify":
        p.paragraph_format.first_line_indent = Cm(first_line)
    run = p.add_run(text)
    run.bold = bold
    run.italic = italic
    run.font.size = Pt(size)
    return p


def code(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.6)
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.line_spacing = 1.0
    run = p.add_run(text)
    run.font.name = "Consolas"
    run.font.size = Pt(8.5)
    rpr = run._element.get_or_add_rPr()
    rfonts = OxmlElement("w:rFonts")
    rfonts.set(qn("w:ascii"), "Consolas")
    rfonts.set(qn("w:hAnsi"), "Consolas")
    rpr.append(rfonts)
    ppr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), "F2F2F2")
    ppr.append(shd)


def caption(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(10)
    run = p.add_run(text)
    run.italic = True
    run.font.size = Pt(10)


def heading(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.name = "Times New Roman"
        run.font.color.rgb = RGBColor(0, 0, 0)
        run.font.size = Pt(16 if level == 1 else 13)
    h.paragraph_format.space_before = Pt(14 if level == 1 else 10)
    h.paragraph_format.space_after = Pt(6)


def add_page_number(paragraph):
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_end)
    run.font.size = Pt(10)


def build_docx(network_png: Path, diagnosis_png: Path, out: Path):
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(1.5)
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)

    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    normal.paragraph_format.space_after = Pt(6)

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_page_number(footer)

    # ------------------------- Титульный лист -------------------------
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(90)
    run = p.add_run("ОТЧЁТ")
    run.bold = True
    run.font.size = Pt(30)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("по лабораторной работе № 39")
    run.font.size = Pt(18)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(30)
    run = p.add_run("Настройка сетевого доступа к приложению")
    run.bold = True
    run.font.size = Pt(20)

    para(doc, "Дисциплина: «Управление работами и разработка программного обеспечения "
              "облачных систем»", align="center", first_line=0)
    para(doc, "Результат обучения: РО 3.2. Эксплуатировать облачные системы",
         align="center", first_line=0)
    para(doc, "Объект: многокомпонентная система Cloud Application (Docker Compose)",
         align="center", first_line=0)
    doc.add_paragraph()

    t = doc.add_table(rows=4, cols=2)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    rows = [
        ("Выполнил", "студент ______________________"),
        ("Группа", "______________________"),
        ("Проверил", "преподаватель ______________________"),
        ("Дата выполнения", "22.11.2026"),
    ]
    for row, (key, value) in zip(t.rows, rows):
        set_cell_text(row.cells[0], key, bold=True, size=12)
        set_cell_text(row.cells[1], value, size=12)
        row.cells[0].width = Cm(5)
        row.cells[1].width = Cm(10)

    doc.add_paragraph()
    para(doc, "2026", align="center", first_line=0, size=14)

    doc.add_page_break()

    # ------------------------- Содержание -------------------------
    heading(doc, "Содержание", 1)
    contents = [
        "1. Цель работы",
        "2. Среда выполнения и сетевая модель",
        "3. Адреса, интерфейсы и маршруты",
        "4. Исходное состояние Compose и loopback-публикация",
        "5. Изменение публикации порта",
        "6. Проверка доступа с клиентского компьютера",
        "7. Инфраструктурные порты",
        "8. Внутренняя сеть Compose",
        "9. Последовательная диагностика",
        "10. Контролируемый отказ bind-address и восстановление",
        "11. Эксплуатационный сетевой паспорт",
        "12. Самостоятельная проверка сетевого пути",
        "13. Ответы на контрольные вопросы",
        "14. Вывод",
        "Приложение А. Воспроизведение",
        "Приложение Б. Файлы отчёта",
    ]
    for item in contents:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        run = p.add_run(item)
        run.font.size = Pt(12)

    doc.add_page_break()

    # ------------------------- 1. Цель -------------------------
    heading(doc, "1. Цель работы", 1)
    para(doc, "Настроить сетевой доступ к ранее развернутой многокомпонентной системе "
              "Cloud Application: определить адреса и интерфейсы, изменить публикацию "
              "Docker Compose-приложения с loopback-интерфейса на сетевой интерфейс, "
              "проверить TCP- и HTTP-доступ с клиентского адреса, подтвердить "
              "недоступность PostgreSQL и Notification Service снаружи, отработать "
              "контролируемый отказ bind-address и восстановление, заполнить "
              "эксплуатационный сетевой паспорт.")
    para(doc, "Работа продолжает ЛР №38: используется Compose-система с сервисами "
              "app, db, notification и одноразовым migrate. Настройка firewall и "
              "ограничений доступа намеренно не выполняется — это содержание ЛР №40.")

    # ------------------------- 2. Среда -------------------------
    heading(doc, "2. Среда выполнения и сетевая модель", 1)
    para(doc, "Отдельная VirtualBox VM отсутствовала, поэтому работа выполнена на "
              "Windows-host с Docker Desktop 29.9.3 (Linux containers). Вместо "
              "Host-only Adapter используется сетевой IPv4-адрес Windows "
              "192.168.0.10/24: он не является loopback и требует явной публикации "
              "Docker-порта, поэтому демонстрирует те же свойства. NAT-доступ в "
              "Интернет обеспечивает обычное подключение Windows. Порт проверяется "
              "с того же компьютера по сетевому адресу, а не по 127.0.0.1; второй "
              "клиентский компьютер в среде отсутствовал. Это отклонение "
              "зафиксировано в паспорте.")
    table(doc, ["Параметр", "Принятое значение", "Фактически"], [
        ("ОС клиента и сервера", "Linux-VM + Docker", "Windows 10 + Docker Desktop 29.9.3"),
        ("Менеджер контейнеров", "Docker Engine", "Docker Engine в Linux-VM Docker Desktop"),
        ("Лабораторный интерфейс", "Host-only Adapter", "«Беспроводная сеть 2»"),
        ("Адрес интерфейса", "VM_LAB_IP", "192.168.0.10"),
        ("Маска", "/24", "255.255.255.0"),
        ("NAT", "Adapter 1", "Windows-host + служебная Linux-VM"),
        ("Compose project", "cloudapp-lr38", "cloudapp-lr39"),
        ("app", "8000/tcp", "192.168.0.10:8080 → 8000/tcp"),
        ("db", "5432/tcp", "не опубликован"),
        ("notification", "9000/tcp", "не опубликован"),
    ], widths=[4.5, 5.0, 7.0])

    doc.add_picture(str(network_png), width=Cm(16.5))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption(doc, "Рисунок 1 — Сетевой путь от клиентского компьютера к Cloud Application")

    # ------------------------- 3. Адреса -------------------------
    heading(doc, "3. Адреса, интерфейсы и маршруты", 1)
    para(doc, "В Linux-среде адреса определяются командами ip -br addr и ip route; "
              "в используемой Windows-среде их аналогами являются Get-NetIPAddress "
              "и Get-NetRoute. Результаты приведены ниже.")
    code(doc, """PS> Get-NetIPAddress -AddressFamily IPv4 |
        Where-Object { $_.IPAddress -notlike '127.*' }
InterfaceAlias       IPAddress       PrefixLength
ZeroTier One         172.27.170.85   16
vEthernet (WSL)      172.18.112.1    20
Беспроводная сеть 2  192.168.0.10    24
Ethernet             10.10.1.61      22

PS> Get-NetRoute -AddressFamily IPv4 |
        Where-Object { $_.DestinationPrefix -in @('0.0.0.0/0','192.168.0.0/24') }
DestinationPrefix NextHop        InterfaceAlias       RouteMetric
192.168.0.0/24    0.0.0.0        Беспроводная сеть 2  256
0.0.0.0/0         192.168.0.1    Беспроводная сеть 2  0""")
    table(doc, ["Параметр", "Значение"], [
        ("Лабораторный интерфейс", "«Беспроводная сеть 2»"),
        ("IPv4-адрес", "192.168.0.10"),
        ("Маска подсети", "255.255.255.0 (/24)"),
        ("Шлюз", "192.168.0.1"),
        ("Connected route", "192.168.0.0/24 → on-link (интерфейс)"),
        ("Default route", "0.0.0.0/0 → 192.168.0.1, metric 0"),
        ("NAT IPv4 (Ethernet)", "10.10.1.61/22"),
    ], widths=[6.0, 10.0])
    para(doc, "VM_LAB_IP=192.168.0.10. Адрес принадлежит физическому интерфейсу, не "
              "является loopback и не используется служебной сетью WSL. Firewall в "
              "ЛР №39 не изменялся.")

    # ------------------------- 4. Исходное состояние -------------------------
    heading(doc, "4. Исходное состояние Compose и loopback-публикация", 1)
    para(doc, "Перед работой одиночный контейнер ЛР №37 был остановлен, чтобы "
              "освободить порт 8080; image cloud-application:0.7 сохранён.")
    code(doc, """$ docker compose -p cloudapp-lr39 ps
NAME                           SERVICE        STATUS        PORTS
cloudapp-lr39-app-1            app            Up (healthy)  127.0.0.1:8080->8000/tcp
cloudapp-lr39-db-1             db             Up (healthy)  5432/tcp
cloudapp-lr39-notification-1   notification   Up            8000/tcp

$ docker compose port app 8000
127.0.0.1:8080

$ Get-NetTCPConnection -State Listen -LocalPort 8080
LocalAddress LocalPort OwningProcess
127.0.0.1         8080         15116

$ curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8080/status
200
$ curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8080/docs
200""")
    para(doc, "Исходная проверка с сетевого адреса:")
    code(doc, """$ Test-NetConnection -ComputerName 192.168.0.10 -Port 8080 -InformationLevel Quiet
False
$ curl --max-time 5 http://192.168.0.10:8080/status
curl: (7) Failed to connect to 192.168.0.10:8080 ... Could not connect to server""")
    para(doc, "Процесс работает и отвечает локально, но loopback-публикация недоступна "
              "по сетевому адресу. Это исходное состояние до изменения Compose.")

    # ------------------------- 5. Изменение -------------------------
    heading(doc, "5. Изменение публикации порта", 1)
    para(doc, "В compose.yaml сервис app переведён на переменную host bind:")
    code(doc, """    ports:
      - "${APP_PUBLISH_IP}:8080:8000\"""")
    para(doc, "Рядом с compose.yaml создан .env, содержащий только Compose-переменную:")
    code(doc, "APP_PUBLISH_IP=192.168.0.10")
    para(doc, "Runtime-параметры приложения остаются в отдельном файле "
              "deploy/etc/cloud-application.env, подключённом как env_file сервисов "
              "app и migrate. Это два разных механизма:")
    table(doc, ["Файл", "Кто читает", "Назначение"], [
        (".env", "Docker Compose", "подстановка ${APP_PUBLISH_IP} в compose.yaml"),
        ("deploy/etc/cloud-application.env", "контейнер (env_file)",
         "runtime-параметры приложения (APP_*, DB_*, LOG_LEVEL)"),
    ], widths=[6.0, 4.5, 6.5])
    para(doc, "Пересоздаётся только сервис app:")
    code(doc, """$ docker compose config --quiet
(ошибок нет)
$ docker compose up -d --force-recreate app

$ docker compose port app 8000
192.168.0.10:8080
$ Get-NetTCPConnection -State Listen -LocalPort 8080
LocalAddress LocalPort OwningProcess
192.168.0.10      8080         15116
$ docker compose ps
app            Up (healthy)   192.168.0.10:8080->8000/tcp
db             Up (healthy)   5432/tcp
notification   Up             8000/tcp""")
    para(doc, "После смены bind обращение к 127.0.0.1:8080 перестаёт работать "
              "(status=000), что подтверждает: Docker слушает только выбранный адрес. "
              "Для применения нового mapping контейнер необходимо пересоздать; "
              "docker compose restart этого не делает.")

    # ------------------------- 6. Клиент -------------------------
    heading(doc, "6. Проверка доступа с клиентского компьютера", 1)
    code(doc, """$ Test-NetConnection -ComputerName 192.168.0.10 -Port 8080
TcpTestSucceeded : True

$ curl.exe --noproxy "*" -i http://192.168.0.10:8080/status
HTTP/1.1 200 OK
server: uvicorn
content-type: application/json
{"status":"ok","service":"CloudApplication","environment":"production",
 "debug":false,"api_prefix":"/api"}

$ Invoke-WebRequest -UseBasicParsing -Uri http://192.168.0.10:8080/docs
StatusCode
200""")
    para(doc, "Swagger UI доступен по адресу http://192.168.0.10:8080/docs; GET /status "
              "выполняется из браузера.")

    # ------------------------- 7. Порты -------------------------
    heading(doc, "7. Инфраструктурные порты", 1)
    code(doc, """$ docker inspect cloudapp-lr39-db-1 --format '{{json .NetworkSettings.Ports}}'
{"5432/tcp":null}
$ docker inspect cloudapp-lr39-notification-1 --format '{{json .NetworkSettings.Ports}}'
{"8000/tcp":null}
$ docker compose port notification 9000
no port 9000/tcp for container cloudapp-lr39-notification-1: 8000/tcp
$ curl --max-time 5 http://192.168.0.10:9000/status
curl: (7) Failed to connect ... Could not connect to server

$ Test-NetConnection -ComputerName 192.168.0.10 -Port 5432 -InformationLevel Quiet
False""")
    para(doc, "Особенность среды: на Windows-host порт 5432 постоянно занимает "
              "посторонний контейнер ticket-postgres (0.0.0.0:5432->5432/tcp) из "
              "другого учебного проекта, не относящийся к cloudapp-lr39. Чтобы "
              "проверка отражала именно наш стек, контейнер был приостановлен на "
              "несколько секунд, проверка выполнена, затем контейнер возвращён в "
              "состояние running. Независимо от этого docker inspect нашего db "
              "показывает {\"5432/tcp\":null}.")
    para(doc, "Команда docker compose port db 5432 в Compose v5 печатает :0 — это "
              "особенность вывода для сервиса без публикации; авторитетным "
              "подтверждением служит NetworkSettings.Ports = null и колонка PORTS в "
              "docker compose ps (5432/tcp без host-адреса).")
    table(doc, ["Источник", "Адрес", "Порт", "Ожидание", "Факт"], [
        ("Windows-клиент", "192.168.0.10", "8080", "доступен", "доступен (TCP True, HTTP 200)"),
        ("Windows-клиент", "192.168.0.10", "5432", "недоступен", "недоступен"),
        ("Windows-клиент", "192.168.0.10", "9000", "недоступен", "недоступен"),
        ("app container", "db", "5432", "доступен", "доступен (172.18.0.3)"),
        ("app container", "notification", "9000", "доступен", "доступен (172.18.0.2)"),
    ], widths=[3.6, 3.2, 1.8, 3.0, 5.4], size=9.5)

    # ------------------------- 8. Внутренняя сеть -------------------------
    heading(doc, "8. Внутренняя сеть Compose", 1)
    code(doc, """$ docker compose exec -T app python -c "import socket; print(socket.gethostbyname('db')); print(socket.gethostbyname('notification'))"
172.18.0.3
172.18.0.2

$ docker compose exec -T app python -c "import httpx; print(httpx.get('http://notification:9000/status').json())"
{'service': 'notification', 'status': 'running'}""")
    para(doc, "Внешняя и внутренняя схемы разделены: наружу опубликован только app:8080, "
              "а app обращается к db и notification по внутренним DNS-именам Compose.")

    # ------------------------- 9. Диагностика -------------------------
    heading(doc, "9. Последовательная диагностика", 1)
    doc.add_picture(str(diagnosis_png), width=Cm(14.5))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption(doc, "Рисунок 2 — Последовательность диагностики сетевого доступа")
    table(doc, ["Уровень", "Инструмент", "Что проверяет", "Результат"], [
        ("1. Клиент", "Test-NetConnection, curl", "адрес и TCP-порт", "True, HTTP 200"),
        ("2. Интерфейс", "Get-NetIPAddress, Get-NetRoute", "наличие адреса и маршрут",
         "192.168.0.10/24"),
        ("3. Host-порт", "Get-NetTCPConnection (аналог ss -ltn)",
         "на каком адресе слушает Docker", "192.168.0.10:8080"),
        ("4. Mapping", "docker compose port app 8000", "host→container", "192.168.0.10:8080"),
        ("5. Контейнер", "docker compose ps, logs", "состояние и журнал",
         "Up (healthy), Uvicorn 0.0.0.0:8000"),
        ("6. Изнутри", "exec + внутренний /status", "исправность FastAPI", "HTTP 200"),
    ], widths=[2.8, 5.0, 5.2, 4.0], size=9.5)
    para(doc, "Если внутренний /status работает, а внешний TCP — нет, проблема находится "
              "на участке container port → Docker publication → host network → client, "
              "а не в приложении.")

    # ------------------------- 10. Отказ -------------------------
    heading(doc, "10. Контролируемый отказ bind-address и восстановление", 1)
    para(doc, "Bind возвращён на loopback только через .env, без изменения кода и образа:")
    code(doc, """APP_PUBLISH_IP=127.0.0.1

$ docker compose up -d --force-recreate app
$ docker compose port app 8000
127.0.0.1:8080
$ curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8080/status
200
$ Test-NetConnection -ComputerName 192.168.0.10 -Port 8080 -InformationLevel Quiet
False
$ curl --max-time 5 http://192.168.0.10:8080/status
curl: (7) Failed to connect ... Could not connect to server""")
    para(doc, "Зафиксировано: контейнер работает, healthcheck успешен, локальный HTTP "
              "отвечает, внешний TCP — нет, docker compose port показывает loopback. "
              "Первопричина — host bind-address, а не FastAPI, контейнер или PostgreSQL.")
    para(doc, "Восстановление рабочего bind:")
    code(doc, """APP_PUBLISH_IP=192.168.0.10

$ docker compose up -d --force-recreate app
$ docker compose port app 8000
192.168.0.10:8080
$ Test-NetConnection -ComputerName 192.168.0.10 -Port 8080
TcpTestSucceeded : True
$ curl -s -o /dev/null -w '%{http_code}' http://192.168.0.10:8080/status
200
$ curl -s -o /dev/null -w '%{http_code}' http://192.168.0.10:8080/docs
200""")

    # ------------------------- 11. Паспорт -------------------------
    heading(doc, "11. Эксплуатационный сетевой паспорт", 1)
    table(doc, ["Параметр", "Фактическое значение"], [
        ("hostname", "DESKTOP-3FUHFLF"),
        ("NAT-интерфейс", "Windows-host + Docker Desktop (Linux VM)"),
        ("NAT IPv4", "10.10.1.61/22 (Ethernet)"),
        ("Лабораторный интерфейс", "«Беспроводная сеть 2»"),
        ("VM/host lab IPv4", "192.168.0.10"),
        ("Маска лабораторной сети", "255.255.255.0 (/24)"),
        ("Шлюз", "192.168.0.1"),
        ("default route", "0.0.0.0/0 → 192.168.0.1"),
        ("Compose project", "cloudapp-lr39"),
        ("app container port", "8000"),
        ("app host bind", "192.168.0.10:8080"),
        ("db", "не опубликован ({\"5432/tcp\":null})"),
        ("notification", "не опубликован"),
        ("/status", "200"),
        ("/docs", "200"),
    ], widths=[6.0, 10.0])

    # ------------------------- 12. Самостоятельная -------------------------
    heading(doc, "12. Самостоятельная проверка сетевого пути", 1)
    table(doc, ["Этап", "Инструмент", "Результат"], [
        ("Адрес клиента и сервера", "Get-NetIPAddress", "192.168.0.10/24"),
        ("ICMP (вспомогательно)", "ping 192.168.0.10", "отвечает"),
        ("TCP 8080", "Test-NetConnection", "True"),
        ("HTTP /status", "curl / Invoke-WebRequest", "200"),
        ("Swagger UI", "браузер /docs", "открывается"),
        ("TCP 5432", "Test-NetConnection", "False"),
        ("TCP 9000", "Test-NetConnection", "False"),
        ("Внутренний DNS", "socket.gethostbyname", "db, notification разрешаются"),
        ("Внутренний HTTP notification", "httpx", "status=running"),
    ], widths=[5.5, 5.0, 6.5])

    # ------------------------- 13. Вопросы -------------------------
    heading(doc, "13. Ответы на контрольные вопросы", 1)
    qa = [
        ("Что называется сетевым интерфейсом?",
         "Программная точка подключения узла к сети (физический адаптер, виртуальный адаптер, loopback), которой назначаются адреса и через которую идёт трафик."),
        ("Что представляет собой IPv4-адрес?",
         "32-битный логический адрес узла в сети, записываемый четырьмя октетами."),
        ("Для чего используется маска сети?",
         "Определяет, какая часть адреса относится к сети, а какая — к узлу, и задаёт размер подсети."),
        ("Что показывает ip -br addr?",
         "Краткий список интерфейсов с их IPv4/IPv6-адресами и состоянием."),
        ("Что показывает ip route?",
         "Таблицу маршрутизации: через какие интерфейсы и шлюзы достигаются сети."),
        ("Что называется default route?",
         "Маршрут по умолчанию для адресов, не попавших в известные сети; обычно ведёт через NAT-шлюз."),
        ("Для чего в лабораторной VM используется NAT?",
         "Транслирует адреса VM в адрес host-компьютера и даёт VM доступ в Интернет без отдельного публичного адреса."),
        ("Для чего используется Host-only Adapter?",
         "Создаёт изолированную виртуальную сеть между host и VM, не выходящую в физическую LAN."),
        ("Чем Host-only отличается от Bridged networking?",
         "Bridged подключает VM напрямую к физической сети и делает её видимой другим устройствам; Host-only оставляет трафик внутри host+VM."),
        ("Почему в ЛР №39 Host-only безопаснее Bridged?",
         "Учебный HTTP-сервис не публикуется в сеть колледжа, поэтому доступ к нему ограничен host-компьютером и его VM."),
        ("Что представляет собой loopback?",
         "Виртуальный интерфейс узла, через который процесс обращается к самому себе."),
        ("Какой IPv4-адрес обычно используется для loopback?",
         "127.0.0.1 (диапазон 127.0.0.0/8)."),
        ("Почему 127.0.0.1:8080 недоступен с Windows-host?",
         "Docker слушает только 127.0.0.1, который существует лишь внутри узла; с другого компьютера этот адрес указывает на него самого."),
        ("Что означает Docker mapping 127.0.0.1:8080:8000?",
         "Host 127.0.0.1:8080 перенаправляется на container 8000."),
        ("Что означает mapping VM_IP:8080:8000?",
         "Host слушает сетевой адрес VM на 8080 и перенаправляет на container 8000, поэтому сервис доступен извне."),
        ("Что представляет собой container port?",
         "Порт, который слушает процесс внутри контейнера (здесь 8000)."),
        ("Что представляет собой host port?",
         "Порт на хосте, публикуемый Docker и принимающий внешние соединения (здесь 8080)."),
        ("Почему приложение внутри контейнера слушает 0.0.0.0:8000?",
         "Чтобы принимать соединения на всех интерфейсах контейнера; иначе Docker не сможет доставить трафик опубликованного порта."),
        ("Почему host bind может быть конкретным IP?",
         "Чтобы ограничить публикацию одним интерфейсом — loopback, LAN или Host-only."),
        ("Что произойдёт, если host IP в Docker mapping не соответствует нужному интерфейсу?",
         "Порт будет слушаться на другом адресе; клиент по ожидаемому адресу получит отказ, хотя контейнер работает."),
        ("Для чего используется docker compose port?",
         "Показывает фактическое host-отображение порта сервиса."),
        ("Что показывает ss -ltn?",
         "Список слушающих TCP-сокетов с локальными адресами и портами."),
        ("Для чего используется Test-NetConnection?",
         "Проверяет разрешение имени, маршрут и TCP-соединение с указанным портом."),
        ("Чем проверка TCP отличается от HTTP-проверки?",
         "TCP проверяет только установку соединения; HTTP — ещё и корректный ответ приложения."),
        ("Почему успешный ping не гарантирует доступность HTTP?",
         "ICMP может проходить, но HTTP-сервис не запущен, слушает другой порт или блокируется firewall."),
        ("Почему неуспешный ping не всегда доказывает недоступность TCP?",
         "ICMP часто фильтруется, при этом TCP-порт может быть доступен."),
        ("Что означает TcpTestSucceeded=True?",
         "TCP-соединение с указанным адресом и портом установлено."),
        ("Почему PostgreSQL не публикуется на host?",
         "БД нужна только приложению; публикация создаёт лишнюю поверхность атаки."),
        ("Почему Notification Service не публикуется на host?",
         "Это внутренний сервис, доступный только через app по внутренней сети Compose."),
        ("Каким образом app обращается к PostgreSQL?",
         "По имени db:5432 внутри сети Compose."),
        ("Каким образом app обращается к Notification Service?",
         "По адресу http://notification:9000 внутри сети Compose."),
        ("Почему внутренние DNS-имена Compose не используются клиентским Windows-компьютером?",
         "Они существуют только в сети Docker; Windows-клиент не подключён к ней и не может их разрешить."),
        ("Для чего используется .env рядом с compose.yaml?",
         "Хранит переменные для подстановки в compose.yaml (здесь APP_PUBLISH_IP)."),
        ("Чем Compose .env отличается от env_file сервиса?",
         ".env читает Compose для интерполяции; env_file передаёт переменные внутрь контейнера."),
        ("Почему после изменения port mapping контейнер необходимо пересоздать?",
         "Port mapping фиксируется при создании контейнера; изменение требует нового контейнера."),
        ("Достаточно ли команды docker compose restart для применения нового mapping?",
         "Нет: restart не пересоздаёт контейнер и не применяет новый mapping."),
        ("Почему диагностика начинается с клиента?",
         "Это сразу отделяет проблему клиента или сети от проблемы сервера."),
        ("Что проверяется командой ip -br addr?",
         "Наличие и состояние адресов на интерфейсах."),
        ("Что проверяется командой ss?",
         "Слушающие сокеты и их локальные адреса и порты."),
        ("Что проверяется командой docker compose port?",
         "Соответствие опубликованного host-порта container-порту."),
        ("Что позволяет доказать внутренний /status контейнера?",
         "Что приложение и контейнер исправны; проблема локализуется в публикации или сети."),
        ("Как контролируемый loopback-эксперимент помогает локализовать проблему?",
         "При исправном приложении и отсутствии внешнего доступа он однозначно указывает на host bind-address."),
    ]
    for number, (question, answer) in enumerate(qa, start=1):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.1
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        r1 = p.add_run(f"{number}. {question} ")
        r1.bold = True
        r1.font.size = Pt(11)
        r2 = p.add_run(answer)
        r2.font.size = Pt(11)

    # ------------------------- 14. Вывод -------------------------
    heading(doc, "14. Вывод", 1)
    para(doc, "Compose-система Cloud Application опубликована на сетевом адресе "
              "192.168.0.10:8080 через переменную APP_PUBLISH_IP; приложение healthy, "
              "/status и /docs отвечают 200 с клиентского адреса. PostgreSQL и "
              "Notification Service наружу не опубликованы и доступны только по "
              "внутренним DNS-именам db и notification. Выполнена последовательная "
              "диагностика от клиента до контейнера. Контролируемый возврат bind на "
              "127.0.0.1 подтвердил, что причиной недоступности является именно host "
              "bind-address, а после восстановления внешний доступ вернулся. "
              "Firewall-ограничения не настраивались — это граница ЛР №40.")

    # ------------------------- Приложения -------------------------
    heading(doc, "Приложение А. Воспроизведение", 1)
    para(doc, "Полный журнал выполнения находится в docs/lr39_evidence.txt. "
              "Автоматизированный сценарий:")
    code(doc, """cd labs/lab-39
bash scripts/lr39/run_lab39.sh""")
    para(doc, "Скрипт создаёт учебные секреты (если их нет), поднимает Compose-стек, "
              "выполняет исходную проверку, меняет APP_PUBLISH_IP, проверяет TCP/HTTP "
              "с сетевого адреса, подтверждает непубликацию db и notification, "
              "проходит диагностику, воспроизводит loopback-отказ и восстанавливает "
              "bind. Стек остаётся запущенным для ЛР №40.")
    para(doc, "Остановка:")
    code(doc, "docker compose -p cloudapp-lr39 down")

    heading(doc, "Приложение Б. Файлы отчёта", 1)
    table(doc, ["Файл", "Содержание"], [
        ("labs/lab-39/compose.yaml", "Compose-система с ${APP_PUBLISH_IP}"),
        ("labs/lab-39/.env", "только APP_PUBLISH_IP (не коммитится)"),
        ("labs/lab-39/deploy/etc/cloud-application.env", "runtime-параметры (env_file)"),
        ("labs/lab-39/scripts/lr39/run_lab39.sh", "автоматизированный сценарий ЛР"),
        ("labs/lab-39/docs/lr39_evidence.txt", "полный журнал выполнения"),
        ("labs/lab-39/docs/lr39_report.docx", "настоящий отчёт"),
    ], widths=[8.5, 7.5])

    doc.core_properties.title = "Отчёт по лабораторной работе № 39"
    doc.core_properties.subject = "Настройка сетевого доступа к приложению"
    doc.core_properties.author = "Cloud Application project"
    doc.save(out)


if __name__ == "__main__":
    network = DOCS / "lr39_network_path.png"
    diagnosis = DOCS / "lr39_diagnosis.png"
    build_network_diagram(network)
    build_diagnosis_diagram(diagnosis)
    out = DOCS / "lr39_report.docx"
    build_docx(network, diagnosis, out)
    print(f"OK: {out} ({out.stat().st_size} bytes)")
