#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Понижение PDF/A-3 -> PDF/A-1 для случаев, которые НЕ берёт браузерный перелейбл:
object/xref-стримы, вложенные файлы и (через Ghostscript) прозрачность.

Использование:
    python pdfa_downgrade.py входной.pdf [выходной.pdf]

Стратегия (от надёжного к запасному):
  1. Если в системе есть Ghostscript — делаем настоящую пересборку в PDF/A-1b.
     Это самый честный путь: флаттенит прозрачность, нормализует структуру,
     встраивает OutputIntent (sRGB).
  2. Иначе используем pikepdf (обёртка над qpdf): отключаем object/xref-стримы,
     удаляем вложения, ставим версию 1.4 и правим XMP pdfaid -> part 1 / conf B.
     Прозрачность так НЕ убирается — об этом честно предупреждаем.

После конвертации обязательно проверь результат:
    verapdf --flavour 1b выходной.pdf
"""
import os
import re
import shutil
import subprocess
import sys


def find_ghostscript():
    for name in ("gswin64c", "gswin32c", "gs"):
        path = shutil.which(name)
        if path:
            return path
    return None


def via_ghostscript(gs, src, dst):
    cmd = [
        gs,
        "-dPDFA=1",
        "-dBATCH",
        "-dNOPAUSE",
        "-dNOOUTERSAVE",
        "-dPDFACompatibilityPolicy=1",
        "-sColorConversionStrategy=UseDeviceIndependentColor",
        "-sDEVICE=pdfwrite",
        "-sOutputFile=" + dst,
        src,
    ]
    print("-> Ghostscript:")
    print("   " + " ".join(cmd))
    subprocess.run(cmd, check=True)
    print("- собран PDF/A-1b через Ghostscript (прозрачность сфлаттенена).")


def via_pikepdf(src, dst):
    import pikepdf

    pdf = pikepdf.open(src)
    root = pdf.Root

    # 1. удалить вложенные файлы (в PDF/A-1 запрещены)
    removed = False
    if "/Names" in root and "/EmbeddedFiles" in root.Names:
        del root.Names.EmbeddedFiles
        removed = True
    if "/AF" in root:
        del root.AF
        removed = True
    for page in pdf.pages:
        if "/AF" in page:
            del page.AF
            removed = True
    if removed:
        print("- удалены вложенные файлы (EmbeddedFiles / AF). Это потеря данных — учти.")

    # 2. XMP: pdfaid part -> 1, conformance -> B
    try:
        with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
            meta["pdfaid:part"] = "1"
            meta["pdfaid:conformance"] = "B"
        print("- XMP помечен как PDF/A-1B.")
    except Exception as e:
        print("! не удалось поправить XMP:", e)

    # 3. переписать без object/xref-стримов и версией 1.4
    pdf.save(
        dst,
        min_version="1.4",
        force_version="1.4",
        object_stream_mode=pikepdf.ObjectStreamMode.disable,
        normalize_content=True,
    )
    print("- структура переписана без object/xref-стримов, версия PDF 1.4.")
    print("! ВНИМАНИЕ: pikepdf не флаттенит прозрачность. Если она была в файле,")
    print("  поставь Ghostscript и запусти снова — тогда получится валидный PDF/A-1.")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    src = sys.argv[1]
    if not os.path.isfile(src):
        print("Файл не найден:", src)
        sys.exit(1)

    if len(sys.argv) > 2:
        dst = sys.argv[2]
    else:
        dst = re.sub(r"\.pdf$", "", src, flags=re.I) + "_PDFA-1.pdf"

    gs = find_ghostscript()
    try:
        if gs:
            via_ghostscript(gs, src, dst)
        else:
            print("Ghostscript не найден — использую pikepdf (структурная правка).")
            via_pikepdf(src, dst)
    except Exception as e:
        print("Ошибка конвертации:", e)
        sys.exit(2)

    print()
    print("Готово:", dst)
    print('Проверь результат:  verapdf --flavour 1b "%s"' % dst)


if __name__ == "__main__":
    main()
