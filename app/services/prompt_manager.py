"""
Сервис для управления системными и пользовательскими промптами
"""
from typing import Optional
from app.extensions import db
from app.models import SystemPrompt, UserPrompt, Stage, User


class PromptManager:
    """
    Менеджер для работы с промптами
    """

    @staticmethod
    def get_system_prompt(stage_id: int) -> Optional[SystemPrompt]:
        """
        Получить системный промпт для этапа

        Args:
            stage_id: ID этапа

        Returns:
            SystemPrompt или None
        """
        return SystemPrompt.query.filter_by(stage_id=stage_id).first()

    @staticmethod
    def get_user_prompt(user_id: int, stage_id: int) -> Optional[UserPrompt]:
        """
        Получить пользовательский промпт для этапа

        Args:
            user_id: ID пользователя
            stage_id: ID этапа

        Returns:
            UserPrompt или None
        """
        return UserPrompt.query.filter_by(user_id=user_id, stage_id=stage_id).first()

    @staticmethod
    def get_or_create_user_prompt(user_id: int, stage_id: int) -> UserPrompt:
        """
        Получить или создать пользовательский промпт
        Если промпта нет - копирует из системного

        Args:
            user_id: ID пользователя
            stage_id: ID этапа

        Returns:
            UserPrompt
        """
        # Проверяем, есть ли уже пользовательский промпт
        user_prompt = UserPrompt.query.filter_by(user_id=user_id, stage_id=stage_id).first()

        if user_prompt:
            return user_prompt

        # Нет - создаём из системного
        system_prompt = SystemPrompt.query.filter_by(stage_id=stage_id).first()

        if not system_prompt:
            raise ValueError(f"Системный промпт для этапа {stage_id} не найден")

        user_prompt = UserPrompt(
            user_id=user_id,
            stage_id=stage_id,
            prompt_text=system_prompt.prompt_text,
            is_customized=False
        )

        db.session.add(user_prompt)
        db.session.commit()

        return user_prompt

    @staticmethod
    def update_system_prompt(stage_id: int, prompt_text: str, description: str = None) -> SystemPrompt:
        """
        Обновить системный промпт

        Args:
            stage_id: ID этапа
            prompt_text: Текст промпта
            description: Описание (опционально)

        Returns:
            SystemPrompt
        """
        system_prompt = SystemPrompt.query.filter_by(stage_id=stage_id).first()

        if system_prompt:
            system_prompt.prompt_text = prompt_text
            if description is not None:
                system_prompt.description = description
        else:
            system_prompt = SystemPrompt(
                stage_id=stage_id,
                prompt_text=prompt_text,
                description=description
            )
            db.session.add(system_prompt)

        db.session.commit()
        return system_prompt

    @staticmethod
    def update_user_prompt(user_id: int, stage_id: int, prompt_text: str) -> UserPrompt:
        """
        Обновить пользовательский промпт

        Args:
            user_id: ID пользователя
            stage_id: ID этапа
            prompt_text: Новый текст промпта

        Returns:
            UserPrompt
        """
        user_prompt = PromptManager.get_or_create_user_prompt(user_id, stage_id)
        user_prompt.prompt_text = prompt_text
        user_prompt.is_customized = True

        db.session.commit()
        return user_prompt

    @staticmethod
    def reset_user_prompt(user_id: int, stage_id: int) -> UserPrompt:
        """
        Сбросить пользовательский промпт к системному

        Args:
            user_id: ID пользователя
            stage_id: ID этапа

        Returns:
            UserPrompt
        """
        system_prompt = SystemPrompt.query.filter_by(stage_id=stage_id).first()

        if not system_prompt:
            raise ValueError(f"Системный промпт для этапа {stage_id} не найден")

        user_prompt = PromptManager.get_or_create_user_prompt(user_id, stage_id)
        user_prompt.prompt_text = system_prompt.prompt_text
        user_prompt.is_customized = False

        db.session.commit()
        return user_prompt

    @staticmethod
    def initialize_user_prompts(user_id: int):
        """
        Инициализировать промпты для нового пользователя
        Копирует все системные промпты

        Args:
            user_id: ID пользователя
        """
        stages = Stage.query.filter_by(is_active=True).all()

        for stage in stages:
            # Создаём промпт только если его еще нет
            existing = UserPrompt.query.filter_by(user_id=user_id, stage_id=stage.id).first()
            if not existing:
                PromptManager.get_or_create_user_prompt(user_id, stage.id)

    @staticmethod
    def get_prompt_for_processing(user_id: int, stage_id: int) -> str:
        """
        Получить промпт для использования в обработке новостей

        Args:
            user_id: ID пользователя
            stage_id: ID этапа

        Returns:
            Текст промпта
        """
        user_prompt = PromptManager.get_or_create_user_prompt(user_id, stage_id)
        return user_prompt.prompt_text