"""
Сервис для конвейерной обработки новостей через выбранные этапы
"""
from typing import List, Dict, Any
from app.models import Stage, StageAssignment, User
from app.services.ai_providers import send_ai_request
from app.services.prompt_manager import PromptManager


class PipelineProcessor:
    """
    Процессор для последовательной обработки новости через выбранные этапы
    """

    @staticmethod
    def process_news(user_id: int, news_text: str, stage_ids: List[int]) -> Dict[str, Any]:
        """
        Обработать новость через выбранные этапы

        Args:
            user_id: ID пользователя
            news_text: Текст новости
            stage_ids: Список ID этапов для обработки

        Returns:
            Dict с результатами обработки:
            {
                "success": bool,
                "results": [
                    {
                        "stage_id": int,
                        "stage_name": str,
                        "stage_display_name": str,
                        "success": bool,
                        "content": str,
                        "model_used": str,
                        "error": str (если есть)
                    }
                ],
                "error": str (общая ошибка, если есть)
            }
        """
        results = {
            "success": True,
            "results": [],
            "error": None
        }

        # Проверяем что этапы выбраны
        if not stage_ids:
            results["success"] = False
            results["error"] = "Не выбраны этапы обработки"
            return results

        # Проверяем что текст новости не пустой
        if not news_text or not news_text.strip():
            results["success"] = False
            results["error"] = "Текст новости не может быть пустым"
            return results

        # Загружаем этапы из БД в правильном порядке
        stages = Stage.query.filter(
            Stage.id.in_(stage_ids),
            Stage.is_active == True
        ).order_by(Stage.order).all()

        if not stages:
            results["success"] = False
            results["error"] = "Выбранные этапы не найдены или неактивны"
            return results

        # Обрабатываем каждый этап последовательно
        for stage in stages:
            stage_result = PipelineProcessor._process_stage(
                user_id=user_id,
                stage=stage,
                news_text=news_text
            )
            results["results"].append(stage_result)

            # Если этап завершился с ошибкой, помечаем общий результат как неуспешный
            if not stage_result["success"]:
                results["success"] = False

        return results

    @staticmethod
    def _process_stage(user_id: int, stage: Stage, news_text: str) -> Dict[str, Any]:
        """
        Обработать один этап

        Args:
            user_id: ID пользователя
            stage: Объект Stage из БД
            news_text: Текст новости

        Returns:
            Dict с результатом обработки этапа
        """
        result = {
            "stage_id": stage.id,
            "stage_name": stage.name,
            "stage_display_name": stage.display_name,
            "success": False,
            "content": None,
            "model_used": None,
            "error": None
        }

        try:
            # Получаем активное назначение модели для этапа
            assignment = StageAssignment.query.filter_by(
                stage_id=stage.id,
                is_active=True
            ).order_by(StageAssignment.priority.desc()).first()

            if not assignment:
                result["error"] = f"Для этапа '{stage.display_name}' не назначена модель"
                return result

            # Получаем промпт для пользователя
            prompt_text = PromptManager.get_prompt_for_processing(user_id, stage.id)

            # Формируем сообщения для AI
            messages = [
                {"role": "system", "content": prompt_text},
                {"role": "user", "content": news_text}
            ]

            # Отправляем запрос к AI (с поддержкой fallback)
            ai_result = send_ai_request(
                model_id=assignment.model_id,
                messages=messages,
                use_fallback=True
            )

            if ai_result["success"]:
                result["success"] = True
                result["content"] = ai_result["content"]
                result["model_used"] = ai_result.get("model", "Unknown")

                # Добавляем информацию о fallback если использовался
                if ai_result.get("fallback_used"):
                    result["fallback_used"] = True
                    result["original_error"] = ai_result.get("original_error")
            else:
                result["error"] = ai_result.get("error", "Неизвестная ошибка AI")

        except Exception as e:
            result["error"] = f"Ошибка обработки: {str(e)}"

        return result

    @staticmethod
    def get_available_stages() -> List[Dict[str, Any]]:
        """
        Получить список доступных активных этапов для отображения в форме

        Returns:
            List с информацией об этапах:
            [
                {
                    "id": int,
                    "name": str,
                    "display_name": str,
                    "description": str,
                    "order": int,
                    "has_model": bool
                }
            ]
        """
        stages = Stage.query.filter_by(is_active=True).order_by(Stage.order).all()

        result = []
        for stage in stages:
            # Проверяем, есть ли активное назначение модели
            has_assignment = StageAssignment.query.filter_by(
                stage_id=stage.id,
                is_active=True
            ).first() is not None

            result.append({
                "id": stage.id,
                "name": stage.name,
                "display_name": stage.display_name,
                "description": stage.description,
                "order": stage.order,
                "has_model": has_assignment
            })

        return result