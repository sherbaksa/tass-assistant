/**
 * Обработка формы отправки новости на конвейер
 */
document.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById('newsProcessingForm');

  // Проверяем, что форма существует на странице
  if (!form) return;

  const submitBtn = document.getElementById('submitBtn');
  const processingStatus = document.getElementById('processingStatus');
  const resultsContainer = document.getElementById('resultsContainer');
  const resultsContent = document.getElementById('resultsContent');
  const newsTextDiv = document.getElementById('newsText');

  // Placeholder для contenteditable
  if (newsTextDiv) {
    newsTextDiv.addEventListener('focus', function() {
      if (this.textContent.trim() === '') {
        this.textContent = '';
      }
    });

    newsTextDiv.addEventListener('blur', function() {
      if (this.textContent.trim() === '') {
        this.classList.add('empty');
      } else {
        this.classList.remove('empty');
      }
    });
  }

  // Логика зависимости чекбоксов
  const freshnessCheckbox = document.querySelector('input[data-stage-name="freshness_check"]');
  const freshnessAnalysisCheckbox = document.querySelector('input[data-stage-name="freshness_analysis"]');
  const freshnessAnalysisLabel = document.querySelector('label[data-stage-name="freshness_analysis"]');

  if (freshnessCheckbox && freshnessAnalysisCheckbox) {
    // Функция обновления состояния зависимого чекбокса
    function updateFreshnessAnalysisState() {
      if (!freshnessCheckbox.checked) {
        freshnessAnalysisCheckbox.checked = false;
        freshnessAnalysisCheckbox.disabled = true;
        if (freshnessAnalysisLabel) {
          freshnessAnalysisLabel.classList.add('disabled');
        }
      } else {
        freshnessAnalysisCheckbox.disabled = false;
        if (freshnessAnalysisLabel) {
          freshnessAnalysisLabel.classList.remove('disabled');
        }
      }
    }

    // Инициализация при загрузке
    updateFreshnessAnalysisState();

    // Обработчик изменения состояния
    freshnessCheckbox.addEventListener('change', updateFreshnessAnalysisState);
  }

  form.addEventListener('submit', async function(e) {
    e.preventDefault();

    // Получаем текст из contenteditable
    const newsText = newsTextDiv.textContent.trim();
    const stageCheckboxes = document.querySelectorAll('input[name="stage_ids"]:checked:not([disabled])');
    const stageIds = Array.from(stageCheckboxes).map(cb => parseInt(cb.value));

    // Валидация
    if (!newsText) {
      alert('Пожалуйста, введите текст новости');
      newsTextDiv.focus();
      return;
    }

    if (stageIds.length === 0) {
      alert('Пожалуйста, выберите хотя бы один этап обработки');
      return;
    }

    // Показываем индикатор загрузки
    submitBtn.disabled = true;
    processingStatus.style.display = 'inline';
    resultsContainer.style.display = 'none';

    try {
      // Получаем CSRF токен
      const csrfToken = document.querySelector('input[name="csrf_token"]')?.value || '';

      // Отправляем запрос
      const response = await fetch(form.dataset.actionUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
          news_text: newsText,
          stage_ids: stageIds
        })
      });

      const data = await response.json();

      // Отображаем результаты
      displayResults(data);

    } catch (error) {
      resultsContent.innerHTML = `
        <div class="alert alert--error">
          Ошибка при обработке: ${error.message}
        </div>
      `;
      resultsContainer.style.display = 'block';
    } finally {
      submitBtn.disabled = false;
      processingStatus.style.display = 'none';
    }
  });

  /**
   * Отображение результатов обработки
   */
  function displayResults(data) {
    if (!data.success && data.error) {
      resultsContent.innerHTML = `
        <div class="alert alert--error">
          ${escapeHtml(data.error)}
        </div>
      `;
      resultsContainer.style.display = 'block';
      return;
    }

    if (!data.results || data.results.length === 0) {
      resultsContent.innerHTML = `
        <div class="alert alert--warning">
          Нет результатов обработки
        </div>
      `;
      resultsContainer.style.display = 'block';
      return;
    }

    // Формируем HTML с результатами
    let html = '';
    data.results.forEach(result => {
      const isSuccess = result.success;
      const itemClass = isSuccess ? 'result-item--success' : 'result-item--error';

      html += `
        <div class="result-item ${itemClass}">
          <div class="result-header">
            <div class="result-title">${escapeHtml(result.stage_display_name)}</div>
            <span class="badge ${isSuccess ? 'badge--success' : 'badge--warning'}">
              ${isSuccess ? '✓ Успешно' : '✗ Ошибка'}
            </span>
          </div>
      `;

      if (isSuccess) {
        html += `
          <div class="result-content">${escapeHtml(result.content)}</div>
          <div class="result-meta">
            Модель: ${escapeHtml(result.model_used || 'Неизвестно')}
            ${result.fallback_used ? ' <span style="color: var(--warn);">(использован резервный вариант)</span>' : ''}
          </div>
        `;
      } else {
        html += `
          <div class="result-error">${escapeHtml(result.error || 'Неизвестная ошибка')}</div>
        `;
      }

      html += `</div>`;
    });

    resultsContent.innerHTML = html;
    resultsContainer.style.display = 'block';

    // Прокручиваем к результатам
    resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  /**
   * Экранирование HTML для безопасного вывода
   */
  function escapeHtml(text) {
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
  }
});