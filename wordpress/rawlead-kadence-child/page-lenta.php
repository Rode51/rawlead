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

$rl_feed_logged_in = isset($_COOKIE['rl_access']) && trim((string) $_COOKIE['rl_access']) !== '';
require_once RAWLEAD_CHILD_DIR . '/template-parts/rawlead/feed-card.php';
$rl_feed_tier = rawlead_feed_tier($rl_feed_logged_in);
$rl_feed_main_class = 'rl-app rl-app--feed site-main';
if ($rl_feed_logged_in) {
	$rl_feed_main_class .= ' rl-app--feed-logged-in';
} else {
	$rl_feed_main_class .= ' rl-app--feed-anon';
}
?>
<main id="primary" class="<?php echo esc_attr($rl_feed_main_class); ?>" data-rl-app="feed" data-feed-tier="<?php echo esc_attr($rl_feed_tier); ?>">
	<?php rawlead_get_part('feed-filter-bar', ['rl_feed_logged_in' => $rl_feed_logged_in, 'rl_feed_tier' => $rl_feed_tier]); ?>
	<?php rawlead_get_part('feed-strip'); ?>
	<div class="rl-container rl-feed-main-wrap">
		<div class="rl-feed-cabinet-bar">
			<a href="<?php echo esc_url(rawlead_page_url('cabinet')); ?>" class="rl-feed-cabinet-bar__link" id="rl-feed-cabinet-link">
				<?php esc_html_e('Кабинет', 'rawlead-kadence-child'); ?> →
			</a>
		</div>
		<header class="rl-feed-head">
			<h1 class="rl-feed-head__title"><?php esc_html_e('Лента заказов', 'rawlead-kadence-child'); ?></h1>
			<div class="rl-feed-head__meta">
				<div class="rl-feed-toolbar" id="rl-feed-toolbar" aria-live="polite"></div>
				<p class="rl-feed-head__count rl-feed-head__count--legacy" id="rl-feed-count" hidden aria-live="polite"></p>
			</div>
		</header>
		<div class="rl-feed-banner" id="rl-feed-error" role="alert" hidden></div>
		<div class="rl-feed-list" id="rl-feed-list" aria-live="polite"></div>
		<div class="rl-feed-pagination" id="rl-feed-pagination">
			<button type="button" class="rl-btn rl-btn--primary rl-btn--load-more" id="rl-feed-load-more">
				<?php esc_html_e('Показать ещё', 'rawlead-kadence-child'); ?> <span class="rl-btn__arrow" aria-hidden="true">→</span>
			</button>
			<span class="rl-feed-pagination__count" id="rl-feed-pagination-count"><?php esc_html_e('Показано', 'rawlead-kadence-child'); ?> <span id="rl-feed-shown">0</span> <?php esc_html_e('из', 'rawlead-kadence-child'); ?> <span id="rl-feed-total">0</span></span>
			<div class="rl-feed-loading" id="rl-feed-loading" role="status" aria-live="polite" hidden>
				<span class="rl-feed-loading__spinner" aria-hidden="true"></span>
				<span class="rl-feed-loading__text"><?php esc_html_e('Подбираем...', 'rawlead-kadence-child'); ?></span>
			</div>
		</div>
		<p class="rl-feed-end" id="rl-feed-end" hidden><?php esc_html_e('Все заказы показаны', 'rawlead-kadence-child'); ?></p>
	</div>
	<div class="rl-feed-skills-modal" id="rl-feed-skills-modal" hidden>
		<div class="rl-feed-skills-modal__overlay" id="rl-feed-skills-modal-overlay" aria-hidden="true"></div>
		<div class="rl-feed-skills-modal__panel rl-skill-tree" role="dialog" aria-modal="true" aria-labelledby="rl-feed-skills-title">
			<div class="rl-skill-tree__handle" aria-hidden="true"></div>
			<header class="rl-skill-tree__header">
				<h3 class="rl-skill-tree__title" id="rl-feed-skills-title"><?php esc_html_e('Навыки', 'rawlead-kadence-child'); ?></h3>
				<p class="rl-skill-tree__counter" id="rl-feed-skill-tree-counter" aria-live="polite"><?php esc_html_e('Выбрано 0 / 12', 'rawlead-kadence-child'); ?></p>
				<button type="button" class="rl-skill-tree__close" id="rl-feed-skill-tree-close" aria-label="<?php esc_attr_e('Закрыть', 'rawlead-kadence-child'); ?>">✕</button>
			</header>
			<p class="rl-skill-tree__hint" id="rl-feed-skill-tree-hint" hidden><?php esc_html_e('Слишком широко — match упадёт. Оставь 6–8 ключевых.', 'rawlead-kadence-child'); ?></p>
			<p class="rl-skill-tree__limit-msg" id="rl-feed-skill-tree-limit" hidden><?php esc_html_e('Максимум 12 — сними лишние.', 'rawlead-kadence-child'); ?></p>
			<div class="rl-skill-tree__body" id="rl-feed-skill-tree-body">
				<div class="rl-skill-tree__roots" id="rl-feed-skill-tree-roots" aria-live="polite"></div>
			</div>
			<footer class="rl-skill-tree__footer">
				<button type="button" class="rl-btn rl-btn--primary rl-feed-skills-apply" id="rl-feed-skills-apply" title="<?php esc_attr_e('Порядок изменится. Заказы не исчезнут.', 'rawlead-kadence-child'); ?>"><?php esc_html_e('Сохранить навыки →', 'rawlead-kadence-child'); ?></button>
				<button type="button" class="rl-skill-tree__reset rl-feed-skills-clear" id="rl-feed-skills-clear"><?php esc_html_e('Сбросить всё', 'rawlead-kadence-child'); ?></button>
			</footer>
		</div>
	</div>
	<div class="rl-feed-sheet" id="rl-feed-sheet" hidden>
		<div class="rl-feed-sheet__overlay" id="rl-feed-sheet-overlay"></div>
		<div class="rl-feed-sheet__panel" role="dialog" aria-modal="true" aria-label="<?php esc_attr_e('Фильтры', 'rawlead-kadence-child'); ?>">
			<div class="rl-feed-sheet__head">
				<span class="rl-feed-sheet__title"><?php esc_html_e('Фильтры', 'rawlead-kadence-child'); ?></span>
				<button type="button" class="rl-feed-sheet__close" id="rl-feed-sheet-close" aria-label="<?php esc_attr_e('Закрыть фильтры', 'rawlead-kadence-child'); ?>">✕</button>
			</div>
			<div class="rl-feed-sheet__body" id="rl-feed-sheet-body"></div>
			<div class="rl-feed-sheet__actions">
				<button type="button" class="rl-btn rl-btn--primary" id="rl-feed-sheet-apply"><?php esc_html_e('Применить →', 'rawlead-kadence-child'); ?></button>
				<button type="button" class="rl-btn rl-btn--ghost" id="rl-feed-sheet-reset"><?php esc_html_e('Сбросить', 'rawlead-kadence-child'); ?></button>
			</div>
		</div>
	</div>
	<div class="rl-feed-quiz-overlay" id="rl-feed-quiz-overlay" hidden aria-hidden="true">
		<div class="rl-feed-quiz-overlay__backdrop" id="rl-feed-quiz-overlay-backdrop" aria-hidden="true"></div>
		<div
			class="rl-feed-quiz-overlay__panel"
			role="dialog"
			aria-modal="true"
			aria-labelledby="rl-quiz-overlay-title"
		>
			<h2 class="rl-feed-quiz-overlay__title" id="rl-quiz-overlay-title">
				<?php esc_html_e('Настройка ленты', 'rawlead-kadence-child'); ?>
			</h2>
			<button
				type="button"
				class="rl-feed-quiz-overlay__close"
				id="rl-feed-quiz-overlay-close"
				aria-label="<?php esc_attr_e('Закрыть', 'rawlead-kadence-child'); ?>"
			>✕</button>
			<div class="rl-feed-quiz-overlay__body">
				<?php rawlead_get_part('quiz', ['rl_quiz_overlay' => true]); ?>
			</div>
		</div>
	</div>
</main>
<?php
rawlead_get_part('footer');
get_footer();
