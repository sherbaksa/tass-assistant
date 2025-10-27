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
        // Пытаемся распарсить JSON и отформатировать
        const formattedContent = formatStageContent(result.stage_name, result.content);

        html += `
          <div class="result-content">${formattedContent}</div>
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
   * Форматирование контента в зависимости от типа этапа
   */
  function formatStageContent(stageName, content) {
    // Убираем markdown блоки кода если есть
    content = content.trim();
    if (content.startsWith('```json') || content.startsWith('```')) {
      content = content.replace(/^```json?\s*/i, '').replace(/```\s*$/, '').trim();
    }

    // Пытаемся распарсить JSON
    let jsonData;
    try {
      jsonData = JSON.parse(content);
    } catch (e) {
      // Если не JSON, возвращаем как есть
      return `<div class="formatted-result">${escapeHtml(content)}</div>`;
    }

    // Форматируем в зависимости от этапа
    switch (stageName) {
      case 'classification':
        return formatClassification(jsonData);
      case 'freshness_check':
        return formatFreshnessCheck(jsonData);
      case 'freshness_analysis':
        return formatFreshnessAnalysis(jsonData);
      case 'analysis':
        return formatAnalysis(jsonData);
      case 'recommendations':
        return formatRecommendations(jsonData);
      default:
        // Красивый JSON fallback
        return `<div class="formatted-result"><pre>${escapeHtml(JSON.stringify(jsonData, null, 2))}</pre></div>`;
    }
  }

  /**
   * Форматирование результатов классификации
   */
  function formatClassification(data) {
    if (!data.codes || !Array.isArray(data.codes)) {
      return '<div class="empty-section">Нет данных о классификации</div>';
    }

    let html = '<div class="formatted-result">';
    html += '<div class="category-list">';

    data.codes.forEach(item => {
      html += `
        <div class="category-item">
          <div class="category-header">
            <span class="category-code">${escapeHtml(item.code)}</span>
            <span class="confidence-badge">
              📊 ${item.confidence}%
            </span>
          </div>
          <div class="category-reasoning">${escapeHtml(item.reasoning)}</div>
        </div>
      `;
    });

    html += '</div></div>';
    return html;
  }

  /**
   * Форматирование проверки на свежесть
   */
  function formatFreshnessCheck(data) {
    let html = '<div class="formatted-result">';

    if (data.search_query) {
      html += `<p><strong>Поисковый запрос:</strong> ${escapeHtml(data.search_query)}</p>`;
    }

    if (data.results && Array.isArray(data.results)) {
      html += `<h3>Найдено публикаций: ${data.results.length}</h3>`;
      // Можно добавить список результатов поиска если нужно
    }

    html += '</div>';
    return html;
  }

  /**
   * Форматирование анализа свежести
   */
  function formatFreshnessAnalysis(data) {
    let html = '<div class="formatted-result">';

    if (data.verdict) {
      html += `
        <div class="overall-verdict">
          <span class="verdict-label">Вердикт:</span>
          <span class="verdict-value">${escapeHtml(data.verdict)}</span>
        </div>
      `;
    }

    if (data.reasoning) {
      html += `<p>${escapeHtml(data.reasoning)}</p>`;
    }

    html += '</div>';
    return html;
  }

  /**
   * Форматирование анализа новости
   */
  function formatAnalysis(data) {
    if (!data.news_analysis) {
      return '<div class="empty-section">Нет данных анализа</div>';
    }

    const analysis = data.news_analysis;
    let html = '<div class="formatted-result">';

    // Общий вердикт и оценка
    if (analysis.overall_verdict || analysis.summary_score) {
      html += '<div class="overall-verdict">';
      if (analysis.overall_verdict) {
        html += `<span class="verdict-label">Вердикт:</span>`;
        html += `<span class="verdict-value">${escapeHtml(analysis.overall_verdict)}</span>`;
      }
      if (analysis.summary_score) {
        html += `<span class="score-badge">${escapeHtml(analysis.summary_score)}</span>`;
      }
      html += '</div>';
    }

    const details = analysis.detailed_analysis;
    if (details) {
      // Фактические ошибки
      if (details.factual_errors && details.factual_errors.length > 0) {
        html += '<h3>⚠️ Фактические ошибки</h3>';
        html += '<div class="issue-list">';
        details.factual_errors.forEach(issue => {
          html += formatIssue(issue);
        });
        html += '</div>';
      } else {
        html += '<h3>✅ Фактические ошибки</h3>';
        html += '<div class="empty-section">Не обнаружено</div>';
      }

      // Стилистические замечания
      if (details.stylistic_issues && details.stylistic_issues.length > 0) {
        html += '<h3>📝 Стилистические замечания</h3>';
        html += '<div class="issue-list">';
        details.stylistic_issues.forEach(issue => {
          html += formatIssue(issue);
        });
        html += '</div>';
      } else {
        html += '<h3>✅ Стилистические замечания</h3>';
        html += '<div class="empty-section">Не обнаружено</div>';
      }

      // Лингвистические ошибки
      if (details.linguistic_errors && details.linguistic_errors.length > 0) {
        html += '<h3>✏️ Лингвистические ошибки</h3>';
        html += '<div class="issue-list">';
        details.linguistic_errors.forEach(issue => {
          html += formatIssue(issue);
        });
        html += '</div>';
      } else {
        html += '<h3>✅ Лингвистические ошибки</h3>';
        html += '<div class="empty-section">Не обнаружено</div>';
      }

      // Оценка тональности
      if (details.tonality_assessment) {
        html += '<h3>🎭 Оценка тональности</h3>';
        html += formatTonality(details.tonality_assessment);
      }
    }

    // Общие комментарии
    if (analysis.general_comments) {
      html += '<div class="general-comments">';
      html += `<strong>💬 Общие комментарии:</strong><br>${escapeHtml(analysis.general_comments)}`;
      html += '</div>';
    }

    html += '</div>';
    return html;
  }

  /**
   * Форматирование одной проблемы/ошибки
   */
  function formatIssue(issue) {
    const severity = (issue.severity || '').toLowerCase();
    const severityClass = severity === 'высокий' || severity === 'high' ? 'high' :
                         severity === 'средний' || severity === 'medium' ? 'medium' : 'low';

    const severityLabel = severity === 'высокий' || severity === 'high' ? 'Высокий' :
                         severity === 'средний' || severity === 'medium' ? 'Средний' : 'Низкий';

    let html = `<div class="issue-item issue-item--${severityClass}">`;
    html += '<div class="issue-header">';
    html += `<span class="issue-type">${escapeHtml(issue.issue_type || 'Замечание')}</span>`;
    html += `<span class="severity-badge severity-badge--${severityClass}">${severityLabel}</span>`;
    html += '</div>';

    if (issue.description) {
      html += `<div class="issue-description">${escapeHtml(issue.description)}</div>`;
    }

    if (issue.text_excerpt) {
      html += `<div class="issue-excerpt">"${escapeHtml(issue.text_excerpt)}"</div>`;
    }

    html += '</div>';
    return html;
  }

  /**
   * Форматирование оценки тональности
   */
  function formatTonality(tonality) {
    let html = '<div class="tonality-assessment">';

    if (tonality.detected_tonality) {
      html += '<div class="tonality-header">';
      html += `<span class="tonality-label">Тональность:</span>`;
      html += `<span class="tonality-value">${escapeHtml(tonality.detected_tonality)}</span>`;
      html += '</div>';
    }

    if (tonality.objectivity_score) {
      html += `<div class="objectivity-score">Объективность: ${escapeHtml(tonality.objectivity_score)}/5</div>`;
    }

    if (tonality.issues && tonality.issues.length > 0) {
      html += '<div class="issue-list" style="margin-top: 12px;">';
      tonality.issues.forEach(issue => {
        html += formatIssue(issue);
      });
      html += '</div>';
    }

    html += '</div>';
    return html;
  }

  /**
   * Форматирование рекомендаций
   */
  function formatRecommendations(data) {
    let html = '<div class="formatted-result">';

    if (data.recommendations && Array.isArray(data.recommendations)) {
      html += '<div class="issue-list">';
      data.recommendations.forEach((rec, idx) => {
        html += `
          <div class="issue-item">
            <div class="issue-header">
              <span class="issue-type">${idx + 1}. Рекомендация</span>
            </div>
            <div class="issue-description">${escapeHtml(rec)}</div>
          </div>
        `;
      });
      html += '</div>';
    } else if (typeof data === 'string') {
      html += `<p>${escapeHtml(data)}</p>`;
    } else {
      html += '<div class="empty-section">Нет рекомендаций</div>';
    }

    html += '</div>';
    return html;
  }

  /**
   * Экранирование HTML для безопасного вывода
   */
  function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
  }
});