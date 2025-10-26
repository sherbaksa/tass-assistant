"""add freshness_analysis stage

Revision ID: e8b078bb3666
Revises: 5ab070e24621
Create Date: 2025-10-26 XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 'e8b078bb3666'
down_revision = '54d8ced98e88'
branch_labels = None
depends_on = None


def upgrade():
    """
    Добавляем новый этап freshness_analysis для анализа результатов поиска.
    Этот этап идёт после freshness_check и является опциональным (отключаемым).
    """
    # Получаем соединение для выполнения запросов
    conn = op.get_bind()

    # Сдвигаем order у существующих этапов, чтобы освободить место
    # freshness_check остаётся на позиции 2
    # freshness_analysis будет на позиции 3
    # analysis сдвигается с 3 на 4
    # recommendations сдвигается с 4 на 5
    conn.execute(
        sa.text("UPDATE stages SET `order` = 5 WHERE name = 'recommendations'")
    )
    conn.execute(
        sa.text("UPDATE stages SET `order` = 4 WHERE name = 'analysis'")
    )

    # Вставляем новый этап
    conn.execute(
        sa.text("""
            INSERT INTO stages (name, display_name, description, `order`, is_active, created_at, updated_at)
            VALUES (
                'freshness_analysis',
                'Анализ результатов поиска',
                'Анализ найденных публикаций для оценки свежести новости',
                3,
                1,
                :created_at,
                :updated_at
            )
        """),
        {"created_at": datetime.utcnow(), "updated_at": datetime.utcnow()}
    )


def downgrade():
    """
    Откат: удаляем freshness_analysis и восстанавливаем порядок этапов
    """
    conn = op.get_bind()

    # Удаляем новый этап (CASCADE удалит связанные промпты и назначения)
    conn.execute(
        sa.text("DELETE FROM stages WHERE name = 'freshness_analysis'")
    )

    # Восстанавливаем исходный порядок
    conn.execute(
        sa.text("UPDATE stages SET `order` = 3 WHERE name = 'analysis'")
    )
    conn.execute(
        sa.text("UPDATE stages SET `order` = 4 WHERE name = 'recommendations'")
    )