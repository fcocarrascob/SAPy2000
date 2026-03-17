# Remove Reportes Module

**Branch:** `feat/reportes_mejora` (already checked out)
**Description:** Completely remove Reportes module backend and GUI from application, keeping focus on SAP2000 interaction only.

## Goal
Remove the entire Reportes module (Word report generation functionality) from the SAP2000 Automation Suite. This functionality has been moved to a separate repository, and this application should remain purely focused on SAP2000 interaction and automation.

## Implementation Steps

### Step 1: Remove Reportes Module
**Files:** 
- `Reportes/` (entire directory)
- `main_app.py` (remove import and tab registration)
- `.github/copilot-instructions.md` (remove Reportes documentation)
- `plans/sapy2000-standardization/step-5-reportes-placeholder.md` (can be deleted or kept for historical reference)

**What:** 
Delete the entire `Reportes/` directory including all Python files (report_backend.py, report_gui.py, word_service.py, equation_translator.py, snippet_manager.py, snippet_editor.py, template_engine.py), data directories (library/, templates/, tests/, deprecated/), and module structure. Remove the Reportes tab from main_app.py by removing the import statement and tab registration. Update copilot-instructions.md to remove all references to Word integration and Reportes module documentation.

**Testing:** 
- [ ] Application launches without errors: `python main_app.py`
- [ ] No Reportes tab appears in the application
- [ ] All other tabs (Combinaciones, Utilidades, Placa Base, Modelo Base, Fundaciones) load correctly
- [ ] No import errors when importing from other modules
- [ ] Verify with: `python -c "from main_app import UnifiedApp; print('OK')"`

## Pre-implementation Questions
[NEEDS CLARIFICATION]
1. Do you want to keep the `plans/sapy2000-standardization/step-5-reportes-placeholder.md` file for historical reference, or should it also be removed?
2. Should we add a note in the README.md at the project root indicating that report generation functionality has been moved to a separate repository? If yes, what's the name/link to that repository?
3. Are there any other documentation files (in docs/ or elsewhere) that reference the Reportes module that should be updated?

## Notes
- The `deprecated/` folder inside Reportes already contains old implementations
- No other modules (Fundaciones, Placa_Base, Modelo_Base, Combinations_Carga, Utilidades_MOD) have any dependencies on Reportes
- The only integration point is in main_app.py (import and tab registration)
- This is a clean removal with no breaking changes to other functionality
