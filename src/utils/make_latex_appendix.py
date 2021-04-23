from json import load
import os

base_name = "Latex_{0}"
base_dir = os.path.join(os.curdir, "150421")

outer_template = """
\\subsection{%s files} \\label{%s}
"""

inner_template = """
\\subsubsection{%s} \\label{%s}

\\begin{itemize}
    \\item MD5 hash: %s
    \\item Content:
\\end{itemize}

\\begin{javascriptcode}
%s
\\end{javascriptcode}
"""

result = ""

for file in os.listdir(os.path.join(base_dir)):
    if not os.path.isdir(os.path.join(base_dir, file)):
        name, extension = file.split(".")
        if extension == "json" and name.__contains__("different"):
            ext = name.split("_")[0]

            result += outer_template % (ext, ext)

            with open(os.path.join(base_dir, file), "r") as f:
                data = load(f)
                file_index = 1
                for res in data["_resources"]:
                    for var in res["_varieties"]:
                        with open(
                            os.path.join(
                                base_dir,
                                "isolated_files",
                                "{0}_file{1}.txt".format(
                                    ext,
                                    file_index
                                    if file_index > 9
                                    else "0" + str(file_index),
                                ),
                            ),
                            "r",
                        ) as f:
                            content = f.read()
                        result += inner_template % (
                            "{0}\_file{1}".format(
                                ext,
                                file_index if file_index > 9 else "0" + str(file_index),
                            ),
                            "{0}\_file{1}".format(
                                ext,
                                file_index if file_index > 9 else "0" + str(file_index),
                            ),
                            var["name"],
                            content,
                        )

with open("test.txt", "w") as f:
    f.write(result)
