"""Batch prediction and manual measurement comparison for the existing app."""
import hashlib
import io
import math

import pandas as pd

MAX_BATCH_ROWS = 200
MAX_CSV_BYTES = 5 * 1024 * 1024


def read_batch_csv(raw):
    if len(raw) > MAX_CSV_BYTES:
        raise ValueError("CSV 文件请控制在 5 MB 以内。")
    if not raw:
        raise ValueError("CSV 文件为空。")
    try:
        decoded = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            decoded = raw.decode("gb18030")
        except UnicodeDecodeError as error:
            raise ValueError("无法读取编码，请将 CSV 保存为 UTF-8。") from error
    try:
        table = pd.read_csv(io.StringIO(decoded), dtype=str, keep_default_na=False)
    except (pd.errors.EmptyDataError, pd.errors.ParserError) as error:
        raise ValueError("无法读取 CSV，请检查表头、引号和列分隔符。") from error
    if table.empty:
        raise ValueError("CSV 只有表头，没有数据行。")
    if len(table) > MAX_BATCH_ROWS:
        raise ValueError(f"本次有 {len(table)} 行；每批最多 {MAX_BATCH_ROWS} 行，请拆分文件。")
    return table


def batch_predict(table, smiles_column, predictor, on_progress=None):
    """Keep every input row, including errors; reuse successful duplicate predictions."""
    cache = {}
    rows = []
    for position, (_, original) in enumerate(table.iterrows(), start=1):
        record = {f"input__{column}": value for column, value in original.items()}
        record.update(row_number=position, status="error", error_message="")
        smiles = str(original[smiles_column]).strip()
        try:
            if not smiles:
                raise ValueError("SMILES 为空")
            if smiles not in cache:
                cache[smiles] = predictor(smiles)
            result = cache[smiles]
            record.update(
                canonical_smiles=result["canonical_smiles"],
                RF_logS=result["rf"]["logS"], RF_mg_L=result["rf"]["mg_L"],
                GNN_logS=result["gnn"]["logS"], GNN_mg_L=result["gnn"]["mg_L"],
                CQR_lower_logS=result["cqr"]["lower_logS"],
                CQR_upper_logS=result["cqr"]["upper_logS"],
                CQR_lower_mg_L=result["cqr"]["lower_mg_L"],
                CQR_upper_mg_L=result["cqr"]["upper_mg_L"],
                atom_count=result["checks"]["atom_count"],
                max_training_similarity=result["checks"]["max_training_similarity"],
                exact_structure_in_training=result["checks"]["exact_structure_in_training"],
                above_training_size=result["checks"]["above_training_size"],
                unseen_elements="; ".join(result["checks"]["unseen_elements"]),
                outside_features="; ".join(result["checks"]["outside_features"]),
                warnings="; ".join(result["checks"]["warnings"]),
                prediction_note=result["prediction_note"], status="success",
            )
        except Exception as error:
            record["error_message"] = f"{type(error).__name__}: {error}"
        rows.append(record)
        if on_progress:
            on_progress(position, len(table))
    return pd.DataFrame(rows)


def measurement_comparison(result, value, unit):
    mw = float(result["descriptors"]["MolWt"])
    if not math.isfinite(mw) or mw <= 0 or not math.isfinite(value):
        raise ValueError("输入值或分子量无效。")
    if unit == "logS（mol/L）":
        log_s = value
        try:
            mg_l = 10 ** value * mw * 1000
        except OverflowError as error:
            raise ValueError("logS 太大，无法换算浓度。") from error
    else:
        if value <= 0:
            raise ValueError("浓度必须大于 0；检出限或范围值不能作为精确实测值。")
        if unit == "mg/L":
            mg_l = value
        elif unit == "g/L":
            mg_l = value * 1000
        elif unit == "mol/L":
            mg_l = value * mw * 1000
        else:
            raise ValueError("不支持的单位。")
        if not math.isfinite(mg_l) or mg_l <= 0:
            raise ValueError("浓度换算超出可表示范围。")
        log_s = math.log10(mg_l / (mw * 1000))
    if not math.isfinite(mg_l) or mg_l <= 0:
        raise ValueError("浓度换算超出可表示范围。")
    rows = []
    for key, label in [("rf", "随机森林 RF"), ("gnn", "图神经网络 GNN")]:
        predicted = float(result[key]["logS"])
        rows.append({"模型": label, "实测 logS": log_s, "预测 logS": predicted,
                     "预测 − 实测（logS）": predicted - log_s,
                     "绝对差（logS）": abs(predicted - log_s)})
    interval = result["cqr"]
    covered = interval["lower_logS"] <= log_s <= interval["upper_logS"]
    return log_s, mg_l, covered, pd.DataFrame(rows)


def render_batch_prediction(predictor):
    from presentation import ui as st
    with st.expander("批量 CSV 预测 · 上传多个分子"):
        st.caption("上传含 SMILES 列的 CSV，手动选择结构列。每批最多 200 行、文件不超过 5 MB。")
        sample = "ID,SMILES\nethanol,CCO\naspirin,CC(=O)Oc1ccccc1C(=O)O\n"
        st.download_button("下载批量输入示例", sample.encode("utf-8-sig"),
                           "solubility_batch_example.csv", "text/csv", key="batch_example")
        upload = st.file_uploader("上传分子 CSV", type=["csv"], key="batch_csv")
        if upload is None:
            st.session_state.pop("batch_prediction_result", None)
            return
        raw = upload.getvalue()
        try:
            table = read_batch_csv(raw)
        except ValueError as error:
            st.session_state.pop("batch_prediction_result", None)
            st.error(str(error))
            return
        columns = list(table.columns)
        default = next((i for i, col in enumerate(columns)
                        if col.strip().casefold() in {"smiles", "canonical_smiles"}), 0)
        column = st.selectbox("选择包含 SMILES 的列", columns, index=default,
                              key="batch_smiles_column")
        signature = hashlib.sha256(raw + column.encode("utf-8")).hexdigest()
        saved = st.session_state.get("batch_prediction_result")
        if saved is not None and saved["signature"] != signature:
            st.session_state.pop("batch_prediction_result", None)
            saved = None
        st.dataframe(table.head(10), hide_index=True, width="stretch")
        st.caption(f"共 {len(table)} 行。失败行会保留并记录原因；输入字段在结果中以 input__ 开头。")
        if st.button("开始批量预测", type="primary", key="run_batch"):
            st.session_state.pop("batch_prediction_result", None)
            progress = st.progress(0.0)
            with st.spinner("正在逐行预测，请等待完成……"):
                output = batch_predict(table, column, predictor,
                    lambda done, total: progress.progress(done / total))
            progress.empty()
            saved = {"signature": signature, "table": output}
            st.session_state["batch_prediction_result"] = saved
        if saved is not None:
            output = saved["table"]
            successful = int(output["status"].eq("success").sum())
            st.write(f"完成：成功 {successful} 行；失败 {len(output) - successful} 行。")
            st.dataframe(output, hide_index=True, width="stretch")
            st.download_button("下载批量预测结果 CSV",
                output.to_csv(index=False).encode("utf-8-sig"),
                "solubility_batch_predictions.csv", "text/csv", key="batch_download")
            st.caption("CQR 区间来自独立分位数模型；目标覆盖率 90%，已记录外部覆盖率 79.6%。预测未指定温度和 pH。")


def render_manual_comparison(result):
    from presentation import ui as st
    structure = result["canonical_smiles"]
    token = hashlib.sha256(structure.encode()).hexdigest()[:16]
    with st.expander("手动输入实验值 · 与当前分子的预测比较"):
        st.code(structure, language=None)
        st.caption("请确认实测值对应上方同一化学结构和化学形式。温度、pH 和来源仅用于记录，不会改变模型预测。")
        with st.form(f"manual_measurement_{token}"):
            unit = st.selectbox("实验值单位", ["mg/L", "g/L", "mol/L", "logS（mol/L）"])
            raw_value = st.text_input("实验溶解度数值", placeholder="例如 2500，支持 2.5e3")
            temperature = st.text_input("温度（°C，可留空）", placeholder="例如 25")
            ph = st.text_input("pH（可留空）", placeholder="未知请留空")
            source = st.text_input("实验来源或文献链接（可留空）")
            submitted = st.form_submit_button("比较实验值与预测")
        storage_key = f"manual_comparison_{token}"
        if submitted:
            st.session_state.pop(storage_key, None)
            try:
                value = float(raw_value.strip())
                temp_value = float(temperature.strip()) if temperature.strip() else None
                ph_value = float(ph.strip()) if ph.strip() else None
                if temp_value is not None and (not math.isfinite(temp_value) or temp_value < -273.15):
                    raise ValueError("温度必须是有效摄氏温度。")
                if ph_value is not None and not math.isfinite(ph_value):
                    raise ValueError("pH 必须是有限数值。")
                log_s, mg_l, covered, comparison = measurement_comparison(result, value, unit)
                comparison["canonical_smiles"] = structure
                comparison["实测 mg/L"] = mg_l
                comparison["输入值"] = value
                comparison["输入单位"] = unit
                comparison["温度 °C"] = temp_value
                comparison["pH"] = ph_value
                comparison["来源"] = source.strip()
                comparison["实测值在 CQR 区间内"] = covered
                st.session_state[storage_key] = {"table": comparison, "covered": covered,
                                                "logS": log_s, "mg_L": mg_l}
            except (ValueError, OverflowError) as error:
                st.error(f"无法比较，请检查数值：{error}")
        saved = st.session_state.get(storage_key)
        if saved is not None:
            # Refresh predictions on reruns while keeping the submitted measurement and provenance.
            comparison = saved["table"].copy()
            for position, key in enumerate(["rf", "gnn"]):
                predicted = result[key]["logS"]
                comparison.loc[position, "预测 logS"] = predicted
                comparison.loc[position, "预测 − 实测（logS）"] = predicted - saved["logS"]
                comparison.loc[position, "绝对差（logS）"] = abs(predicted - saved["logS"])
            covered = result["cqr"]["lower_logS"] <= saved["logS"] <= result["cqr"]["upper_logS"]
            comparison["实测值在 CQR 区间内"] = covered
            st.write(f"实测值换算：{saved['logS']:.4f} logS；{saved['mg_L']:,.4g} mg/L")
            st.dataframe(comparison, hide_index=True, width="stretch")
            st.info("实测值" + ("落在" if covered else "未落在") + "当前 CQR 区间内。单条比较不能证明总体覆盖率。")
            st.caption("正差表示预测偏高，负差表示预测偏低。不同测量条件下的差异不一定全部来自模型误差。")
            st.download_button("下载本次实验值对比 CSV",
                comparison.to_csv(index=False).encode("utf-8-sig"),
                "solubility_manual_comparison.csv", "text/csv", key=f"manual_download_{token}")
