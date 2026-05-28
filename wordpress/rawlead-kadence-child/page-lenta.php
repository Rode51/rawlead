<?php
/**
 * Template: /lenta — открытая лента заказов.
 * Slug «feed» в WP зарезервирован под RSS — страница только «lenta».
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

get_header();
rawlead_get_part('header');
?>
<main id="primary" class="rl-app rl-app--feed site-main" data-rl-app="feed">
	<div class="rl-filter-bar" id="rl-feed-sidebar" aria-label="<?php esc_attr_e('Фильтры', 'rawlead-kadence-child'); ?>">
		<div class="rl-filter-bar__inner" id="rl-feed-sidebar-scroll">
			<fieldset class="rl-feed-filter rl-feed-filter--source is-visually-hidden">
				<legend><?php esc_html_e('Источник', 'rawlead-kadence-child'); ?></legend>
				<label class="rl-feed-chip is-active"><input type="radio" name="source" value="" checked> <?php esc_html_e('Все', 'rawlead-kadence-child'); ?></label>
				<label class="rl-feed-chip"><input type="radio" name="source" value="fl"> FL.ru</label>
				<label class="rl-feed-chip"><input type="radio" name="source" value="kwork"> Kwork</label>
				<label class="rl-feed-chip"><input type="radio" name="source" value="tg"> Telegram</label>
			</fieldset>
			<fieldset class="rl-feed-filter rl-feed-filter--category rl-filter-bar__cats">
				<legend class="screen-reader-text"><?php esc_html_e('Специализация', 'rawlead-kadence-child'); ?></legend>
				<label class="rl-cat-chip is-active" id="filter-category-all">
					<input type="checkbox" name="category" value="" checked>
					<?php esc_html_e('Все', 'rawlead-kadence-child'); ?>
				</label>
				<label class="rl-cat-chip" id="filter-category-dev">
					<input type="checkbox" name="category" value="dev">
					<span class="rl-cat-chip__icon" aria-hidden="true">&lt;/&gt;</span>
					<span class="rl-cat-chip__label rl-cat-chip__label--full"><?php esc_html_e('Разработка', 'rawlead-kadence-child'); ?></span>
					<span class="rl-cat-chip__label rl-cat-chip__label--short"><?php esc_html_e('Код', 'rawlead-kadence-child'); ?></span>
				</label>
				<label class="rl-cat-chip" id="filter-category-design">
					<input type="checkbox" name="category" value="design">
					<span class="rl-cat-chip__icon" aria-hidden="true">✦</span>
					<span class="rl-cat-chip__label rl-cat-chip__label--full"><?php esc_html_e('Дизайн', 'rawlead-kadence-child'); ?></span>
					<span class="rl-cat-chip__label rl-cat-chip__label--short"><?php esc_html_e('Дизайн', 'rawlead-kadence-child'); ?></span>
				</label>
				<label class="rl-cat-chip" id="filter-category-marketing">
					<input type="checkbox" name="category" value="marketing">
					<span class="rl-cat-chip__icon" aria-hidden="true">◎</span>
					<span class="rl-cat-chip__label rl-cat-chip__label--full"><?php esc_html_e('Маркетинг', 'rawlead-kadence-child'); ?></span>
					<span class="rl-cat-chip__label rl-cat-chip__label--short"><?php esc_html_e('SMM', 'rawlead-kadence-child'); ?></span>
				</label>
				<label class="rl-cat-chip" id="filter-category-text">
					<input type="checkbox" name="category" value="text">
					<span class="rl-cat-chip__icon" aria-hidden="true">Aa</span>
					<span class="rl-cat-chip__label rl-cat-chip__label--full"><?php esc_html_e('Тексты', 'rawlead-kadence-child'); ?></span>
					<span class="rl-cat-chip__label rl-cat-chip__label--short"><?php esc_html_e('Тексты', 'rawlead-kadence-child'); ?></span>
				</label>
			</fieldset>
			<div class="rl-filter-bar__actions">
				<details class="rl-feed-skills-dd">
					<summary class="rl-filter-dropdown-btn rl-feed-skills-dd__trigger" id="rl-feed-skills-trigger">
						<span class="rl-feed-skills-dd__label" id="rl-feed-skills-trigger-label"><?php esc_html_e('Навыки ▾', 'rawlead-kadence-child'); ?></span>
						<span class="rl-feed-skills-dd__badge" id="rl-feed-skills-badge" hidden></span>
					</summary>
					<div class="rl-skills-panel rl-feed-skills-dd__panel" id="rl-feed-skills-panel">
						<h3 class="rl-skills-panel__title"><?php esc_html_e('Навыки', 'rawlead-kadence-child'); ?></h3>
						<p class="rl-feed-skills__section" id="rl-feed-skills-section" hidden></p>
						<div class="rl-feed-skills" id="rl-feed-skills" aria-live="polite"></div>
						<button type="button" class="rl-feed-skills-rare" id="rl-feed-skills-rare" hidden><?php esc_html_e('Показать редкие навыки', 'rawlead-kadence-child'); ?></button>
						<p class="rl-feed-skills__hint" id="rl-feed-skills-hint" hidden><?php esc_html_e('Выберите навыки и нажмите Применить', 'rawlead-kadence-child'); ?></p>
						<div class="rl-skills-panel__footer">
							<button type="button" class="rl-btn rl-btn--primary rl-feed-skills-apply" id="rl-feed-skills-apply" title="<?php esc_attr_e('Порядок изменится. Заказы не исчезнут.', 'rawlead-kadence-child'); ?>"><?php esc_html_e('Применить', 'rawlead-kadence-child'); ?></button>
							<button type="button" class="rl-feed-skills-clear" id="rl-feed-skills-clear"><?php esc_html_e('Сбросить', 'rawlead-kadence-child'); ?></button>
						</div>
					</div>
				</details>
				<details class="rl-filter-sort-dd">
					<summary class="rl-filter-dropdown-btn" id="rl-feed-sort-trigger"><?php esc_html_e('Сортировка ▾', 'rawlead-kadence-child'); ?></summary>
					<div class="rl-sort-panel">
						<label class="rl-sort-option is-active"><input type="radio" name="sort" value="time" checked> <?php esc_html_e('Новые сначала', 'rawlead-kadence-child'); ?></label>
						<label class="rl-sort-option"><input type="radio" name="sort" value="match"> <?php esc_html_e('По совместимости', 'rawlead-kadence-child'); ?></label>
					</div>
				</details>
				<button type="button" class="rl-filter-reset rl-feed-reset" hidden><?php esc_html_e('Сбросить фильтры', 'rawlead-kadence-child'); ?></button>
			</div>
		</div>
	</div>
	<p class="rl-sort-badge" id="rl-feed-sort-badge" hidden><?php esc_html_e('Сортировка по совместимости', 'rawlead-kadence-child'); ?></p>
	<div class="rl-container rl-feed-main-wrap">
		<header class="rl-feed-head">
			<h1 class="rl-feed-head__title"><?php esc_html_e('Лента заказов', 'rawlead-kadence-child'); ?></h1>
			<p class="rl-feed-head__count" id="rl-feed-count" aria-live="polite"></p>
			<button type="button" class="rl-btn rl-btn--ghost rl-feed-filters-btn" id="rl-feed-filters-open" aria-expanded="false">
				<?php esc_html_e('Фильтры', 'rawlead-kadence-child'); ?>
			</button>
		</header>
		<div class="rl-feed-banner" id="rl-feed-error" role="alert" hidden></div>
		<div class="rl-feed-list" id="rl-feed-list" aria-live="polite"></div>
		<div class="rl-feed-sentinel" id="rl-feed-sentinel" aria-hidden="true"></div>
		<div class="rl-feed-loading" id="rl-feed-loading" role="status" aria-live="polite" hidden>
			<span class="rl-feed-loading__spinner" aria-hidden="true"></span>
			<span class="rl-feed-loading__text"><?php esc_html_e('Загружаем ещё заказы…', 'rawlead-kadence-child'); ?></span>
		</div>
		<p class="rl-feed-end" id="rl-feed-end" hidden><?php esc_html_e('Все заказы показаны', 'rawlead-kadence-child'); ?></p>
	</div>
	<div class="rl-feed-sheet" id="rl-feed-sheet" hidden>
		<div class="rl-feed-sheet__overlay" id="rl-feed-sheet-overlay"></div>
		<div class="rl-feed-sheet__panel" role="dialog" aria-modal="true" aria-label="<?php esc_attr_e('Фильтры', 'rawlead-kadence-child'); ?>">
			<div class="rl-feed-sheet__body" id="rl-feed-sheet-body"></div>
			<div class="rl-feed-sheet__actions">
				<button type="button" class="rl-btn rl-btn--primary" id="rl-feed-sheet-apply"><?php esc_html_e('Применить', 'rawlead-kadence-child'); ?></button>
				<button type="button" class="rl-btn rl-btn--ghost" id="rl-feed-sheet-reset"><?php esc_html_e('Сбросить', 'rawlead-kadence-child'); ?></button>
			</div>
		</div>
	</div>
	<button type="button" class="rl-bug-fab" id="rl-bug-fab" title="<?php esc_attr_e('Нашли ошибку?', 'rawlead-kadence-child'); ?>" aria-label="<?php esc_attr_e('Сообщить об ошибке', 'rawlead-kadence-child'); ?>">?</button>
	<div class="rl-bug-modal" id="rl-bug-modal" hidden>
		<div class="rl-bug-modal__overlay" id="rl-bug-modal-overlay"></div>
		<div class="rl-bug-modal__panel" role="dialog" aria-modal="true" aria-labelledby="rl-bug-modal-title">
			<h2 class="rl-bug-modal__title" id="rl-bug-modal-title"><?php esc_html_e('Сообщить об ошибке', 'rawlead-kadence-child'); ?></h2>
			<label class="rl-bug-modal__label" for="rl-bug-text"><?php esc_html_e('Что случилось?', 'rawlead-kadence-child'); ?></label>
			<textarea class="rl-bug-modal__input" id="rl-bug-text" rows="4" placeholder="<?php esc_attr_e('Опиши кратко — поможем разобраться', 'rawlead-kadence-child'); ?>"></textarea>
			<p class="rl-bug-modal__url"><span><?php esc_html_e('Страница:', 'rawlead-kadence-child'); ?></span> <span id="rl-bug-url"></span></p>
			<button type="button" class="rl-btn rl-btn--primary" id="rl-bug-submit"><?php esc_html_e('Отправить', 'rawlead-kadence-child'); ?></button>
			<p class="rl-bug-modal__success" id="rl-bug-success" hidden><?php esc_html_e('Спасибо. Посмотрим.', 'rawlead-kadence-child'); ?></p>
		</div>
	</div>
</main>
<?php
rawlead_get_part('footer');
get_footer();
