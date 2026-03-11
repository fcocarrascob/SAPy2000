"""Backend de Combinaciones de Carga — Lógica pura para SAP2000 API."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app_logger import AppLogger
from sap_utils_common import check_ret_code


class ComboBackend:
    def __init__(self, sap_model=None):
        """
        Inicializa el backend.

        Args:
            sap_model: Objeto SapModel opcional ya conectado.
        """
        self.SapModel = sap_model
        self.logger = AppLogger()

    def get_load_cases(self):
        """Retorna una lista con los nombres de todos los Load Cases."""
        if not self.SapModel:
            return []

        try:
            ret = self.SapModel.LoadCases.GetNameList()
            if check_ret_code(ret) and ret[0] > 0:
                names = ret[1]
                if not isinstance(names, (list, tuple)):
                    names = [names]
                return [str(n).strip() for n in names]
        except Exception as e:
            self.logger.error(f"Error obteniendo Load Cases: {e}")
        return []

    def get_combinations(self):
        """
        Retorna lista de dicts con la definición de cada combinación.
        Estructura: [{'name': 'COMB1', 'type': 0, 'items': {'DEAD': 1.2, 'LIVE': 1.6}}, ...]
        """
        if not self.SapModel:
            return []

        combos = []
        try:
            ret_names = self.SapModel.RespCombo.GetNameList()
            if not check_ret_code(ret_names):
                return []
            if ret_names[0] == 0:
                return []

            names = ret_names[1]
            if not isinstance(names, (list, tuple)):
                names = [names]

            for name in names:
                name = str(name).strip()
                # Obtener Tipo
                ret_type = self.SapModel.RespCombo.GetTypeOAPI(name)
                c_type = 0
                if check_ret_code(ret_type):
                    c_type = ret_type[0]

                # Obtener lista de casos dentro de esta combinación
                items = {}
                ret_list = self.SapModel.RespCombo.GetCaseList(name)

                if check_ret_code(ret_list) and ret_list[0] > 0:
                    c_types = ret_list[1]
                    c_names = ret_list[2]
                    sfs = ret_list[3]

                    if not isinstance(c_names, (list, tuple)):
                        c_names = [c_names]
                    if not isinstance(c_types, (list, tuple)):
                        c_types = [c_types]
                    if not isinstance(sfs, (list, tuple)):
                        sfs = [sfs]

                    count = min(len(c_names), len(c_types), len(sfs), ret_list[0])

                    for i in range(count):
                        try:
                            if int(c_types[i]) == 0:
                                name_key = str(c_names[i]).strip()
                                items[name_key] = sfs[i]
                        except Exception:
                            pass

                combos.append({
                    "name": name,
                    "type": c_type,
                    "items": items,
                })

        except Exception as e:
            self.logger.error(f"Error obteniendo combinaciones: {e}")
        return combos

    def _clear_combo_items(self, name):
        """Elimina todos los casos de carga de una combinación existente."""
        try:
            ret_list = self.SapModel.RespCombo.GetCaseList(name)

            if check_ret_code(ret_list) and ret_list[0] > 0:
                c_types = ret_list[1]
                c_names = ret_list[2]

                if not isinstance(c_names, (list, tuple)):
                    c_names = [c_names]
                if not isinstance(c_types, (list, tuple)):
                    c_types = [c_types]

                count = min(len(c_names), len(c_types), ret_list[0])

                for i in range(count):
                    try:
                        self.SapModel.RespCombo.DeleteCase(
                            name, int(c_types[i]), str(c_names[i]).strip()
                        )
                    except Exception:
                        pass
        except Exception as e:
            self.logger.warning(f"Aviso limpiando combinación {name}: {e}")

    def push_combinations(self, combos_data):
        """
        Envía las combinaciones a SAP2000.
        combos_data: lista de dicts {'name': str, 'type': int, 'items': {'CASE': factor}}
        Retorna el número de combinaciones procesadas.
        """
        if not self.SapModel:
            return 0

        success_count = 0

        try:
            self.SapModel.SetModelIsLocked(False)
        except Exception:
            pass

        for combo in combos_data:
            name = str(combo["name"]).strip()
            ctype = int(combo["type"])
            items = combo["items"]

            if not name:
                continue

            ret_add = self.SapModel.RespCombo.Add(name, ctype)
            if isinstance(ret_add, (list, tuple)):
                ret_add = ret_add[-1]

            if ret_add != 0:
                self.SapModel.RespCombo.SetTypeOAPI(name, ctype)
                self._clear_combo_items(name)

            for case_name, factor in items.items():
                try:
                    case_name_clean = str(case_name).strip()
                    val = float(factor)
                    if val != 0:
                        ret_case = self.SapModel.RespCombo.SetCaseList(
                            name, 0, case_name_clean, val
                        )
                        ret_code = ret_case
                        if isinstance(ret_case, (list, tuple)):
                            ret_code = ret_case[-1]
                        if ret_code != 0:
                            self.logger.warning(
                                f"No se pudo asignar '{case_name_clean}' a '{name}' (Código {ret_case})"
                            )
                except Exception as e:
                    self.logger.error(f"Error procesando factor para {case_name}: {e}")

            success_count += 1

        try:
            self.SapModel.View.RefreshView(0, False)
        except Exception:
            pass

        self.logger.success(f"Se procesaron {success_count} combinaciones")
        return success_count