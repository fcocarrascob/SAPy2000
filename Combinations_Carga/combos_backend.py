import comtypes.client

class ComboBackend:
    def __init__(self, sap_model=None):
        """
        Inicializa el backend.
        
        Args:
            sap_model: Objeto SapModel opcional ya conectado. Si es None, intentará conectar.
        """
        self.SapModel = sap_model
        if self.SapModel is None:
            self._connect()

    def _connect(self):
        try:
            # Intentar conectar a instancia activa
            SapObject = comtypes.client.GetActiveObject("CSI.SAP2000.API.SapObject")
            self.SapModel = SapObject.SapModel
            return True
        except Exception:
            self.SapModel = None
            return False

    def get_load_cases(self):
        """Retorna una lista con los nombres de todos los Load Cases."""
        if not self.SapModel: 
            if not self._connect(): return []
            
        try:
            # GetNameList retorna (NumberNames, (Name1, Name2...), RetCode)
            ret = self.SapModel.LoadCases.GetNameList()
            if ret[-1] == 0 and ret[0] > 0:
                names = ret[1]
                # Safety check: comtypes usually returns tuple, but if single item...
                if not isinstance(names, (list, tuple)):
                    names = [names]
                return [str(n).strip() for n in names]
        except Exception as e:
            print(f"Error obteniendo Load Cases: {e}")
        return []

    def get_combinations(self):
        """
        Retorna una lista de diccionarios con la definición de cada combinación.
        Estructura: [{'name': 'COMB1', 'type': 0, 'items': {'DEAD': 1.2, 'LIVE': 1.6}}, ...]
        """
        if not self.SapModel:
            if not self._connect(): return []
            
        combos = []
        try:
            # Obtener nombres de combinaciones
            ret_names = self.SapModel.RespCombo.GetNameList()
            if ret_names[-1] != 0: return []
            if ret_names[0] == 0: return [] # No hay combos
            
            names = ret_names[1]
            if not isinstance(names, (list, tuple)):
                names = [names]

            for name in names:
                name = str(name).strip()
                # Obtener Tipo (0=Linear Additive, 1=Envelope, etc.)
                # GetTypeOAPI(Name) -> (ComboType, Ret)
                ret_type = self.SapModel.RespCombo.GetTypeOAPI(name)
                c_type = 0
                if ret_type[-1] == 0:
                    c_type = ret_type[0]

                # Obtener lista de casos/combos dentro de esta combinación
                # GetCaseList(Name) -> (NumberItems, CName[], CType[], SF[], Ret)
                items = {}
                ret_list = self.SapModel.RespCombo.GetCaseList(name)
                
                # Si ret_list[-1] == 0 y NumberItems > 0
                if ret_list[-1] == 0 and ret_list[0] > 0:
                    # Orden correcto según API: (NumberItems, CType, CName, SF, RetCode)
                    c_types = ret_list[1] # 0=LoadCase, 1=Combo
                    c_names = ret_list[2]
                    sfs = ret_list[3]
                    
                    # Safety for single items or non-iterable returns
                    if not isinstance(c_names, (list, tuple)): c_names = [c_names]
                    if not isinstance(c_types, (list, tuple)): c_types = [c_types]
                    if not isinstance(sfs, (list, tuple)): sfs = [sfs]
                    
                    count = min(len(c_names), len(c_types), len(sfs), ret_list[0])

                    for i in range(count):
                        # Solo nos interesan los Load Cases (Type 0) para la matriz simple
                        # Si es un combo anidado (Type 1), lo ignoramos en esta versión simplificada
                        try:
                            if int(c_types[i]) == 0: 
                                name_key = str(c_names[i]).strip()
                                items[name_key] = sfs[i]
                        except Exception:
                            pass
                
                combos.append({
                    'name': name,
                    'type': c_type,
                    'items': items
                })
        except Exception as e:
            print(f"Error obteniendo combinaciones: {e}")
        return combos

    def _clear_combo_items(self, name):
        """Elimina todos los casos de carga de una combinación existente."""
        try:
            # GetCaseList(Name) -> (NumberItems, CType[], CName[], SF[], Ret)
            ret_list = self.SapModel.RespCombo.GetCaseList(name)
            
            if ret_list[-1] == 0 and ret_list[0] > 0:
                # Orden correcto según API: (NumberItems, CType, CName, SF, RetCode)
                c_types = ret_list[1]
                c_names = ret_list[2]
                
                if not isinstance(c_names, (list, tuple)): c_names = [c_names]
                if not isinstance(c_types, (list, tuple)): c_types = [c_types]
                
                count = min(len(c_names), len(c_types), ret_list[0])
                
                # Eliminar uno por uno
                for i in range(count):
                    try:
                        # DeleteCase(Name, CType, CName)
                        # Usamos strip() para asegurar que el nombre esté limpio
                        self.SapModel.RespCombo.DeleteCase(name, int(c_types[i]), str(c_names[i]).strip())
                    except Exception:
                        # Ignoramos errores puntuales al borrar (puede que ya no exista o esté bloqueado)
                        # De todas formas SetCaseList se encargará de actualizar/agregar
                        pass
        except Exception as e:
            print(f"Aviso limpiando combinación {name}: {e}")

    def push_combinations(self, combos_data):
        """
        Envía las combinaciones a SAP2000.
        combos_data: lista de dicts {'name': str, 'type': int, 'items': {'CASE': factor}}
        """
        if not self.SapModel:
            if not self._connect(): return False
        
        success_count = 0
        
        # Bloquear modelo para velocidad
        try:
            self.SapModel.SetModelIsLocked(False)
        except:
            pass

        for combo in combos_data:
            name = str(combo['name']).strip()
            ctype = int(combo['type'])
            items = combo['items']
            
            if not name: continue

            # Estrategia Robusta: Intentar Agregar, si falla, Actualizar.
            
            # 1. Intentar crear nueva
            ret_add = self.SapModel.RespCombo.Add(name, ctype)
            # Manejo de retorno flexible por si Add retorna tupla (debido a parámetros ByRef implícitos)
            if isinstance(ret_add, (list, tuple)): ret_add = ret_add[-1]
            
            if ret_add != 0:
                # Si falla (probablemente ya existe), actualizamos el tipo
                # SetTypeOAPI(Name, Type)
                self.SapModel.RespCombo.SetTypeOAPI(name, ctype)
                
                # Y limpiamos los items existentes para empezar de cero
                self._clear_combo_items(name)
            
            # 2. Agregar/Actualizar casos
            for case_name, factor in items.items():
                try:
                    case_name_clean = str(case_name).strip()
                    val = float(factor)
                    if val != 0:
                        # SetCaseList(Name, CNameType, CName, SF)
                        # CNameType: 0 = LoadCase
                        # IMPORTANTE: CNameType es ByRef en la API, por lo que comtypes retorna (InputVal, RetCode)
                        ret_case = self.SapModel.RespCombo.SetCaseList(name, 0, case_name_clean, val)
                        
                        ret_code = ret_case
                        if isinstance(ret_case, (list, tuple)):
                            ret_code = ret_case[-1]

                        if ret_code != 0:
                            print(f"Advertencia: No se pudo asignar '{case_name_clean}' a '{name}' (Código {ret_case})")
                except Exception as e:
                    print(f"Error procesando factor para {case_name}: {e}")
            
            success_count += 1
            
        # Refrescar vistas
        try:
            self.SapModel.View.RefreshView(0, False)
        except:
            pass
            
        return success_count
