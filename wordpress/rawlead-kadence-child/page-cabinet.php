<?php
/**
 * Template: /cabinet — персональная лента (final_rank) + теги.
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

get_header();
rawlead_get_part('header');
?>
<main id="primary" class="rl-app rl-app--cabinet site-main" data-rl-app="cabinet">
	<div class="rl-container rl-app__layout">
		<aside class="rl-feed-sidebar" id="rl-cabinet-sidebar" aria-label="<?php esc_attr_e('Фильтры', 'rawlead-kadence-child'); ?>">
			<h2 class="rl-feed-sidebar__title"><?php esc_html_e('Фильтры', 'rawlead-kadence-child'); ?></h2>
			<fieldset class="rl-feed-filter">
				<legend><?php esc_html_e('Источник', 'rawlead-kadence-child'); ?></legend>
				<label class="rl-feed-chip is-active"><input type="radio" name="source" value="" checked> <?php esc_html_e('Все', 'rawlead-kadence-child'); ?></label>
				<label class="rl-feed-chip"><input type="radio" name="source" value="fl"> FL.ru</label>
				<label class="rl-feed-chip"><input type="radio" name="source" value="kwork"> Kwork</label>
				<label class="rl-feed-chip"><input type="radio" name="source" value="tg"> Telegram</label>
			</fieldset>
			<fieldset class="rl-feed-filter">
				<legend><?php esc_html_e('Совместимость', 'rawlead-kadence-child'); ?></legend>
				<label class="rl-feed-chip is-active"><input type="radio" name="min_score" value="0" checked> <?php esc_html_e('Любая', 'rawlead-kadence-child'); ?></label>
				<label class="rl-feed-chip"><input type="radio" name="min_score" value="50"> <?php esc_html_e('От 50%', 'rawlead-kadence-child'); ?></label>
				<label class="rl-feed-chip"><input type="radio" name="min_score" value="70"> <?php esc_html_e('От 70%', 'rawlead-kadence-child'); ?></label>
			</fieldset>
			<button type="button" class="rl-feed-reset rl-link-arrow" hidden><?php esc_html_e('Сбросить фильтры', 'rawlead-kadence-child'); ?></button>
		</aside>
		<div class="rl-feed-main">
			<header class="rl-cabinet-head">
				<h1 class="rl-cabinet-head__title"><?php esc_html_e('Мои заказы', 'rawlead-kadence-child'); ?></h1>
				<p class="rl-cabinet-head__label"><?php esc_html_e('Ваши теги:', 'rawlead-kadence-child'); ?></p>
				<div class="rl-cabinet-tags" id="rl-cabinet-tags" role="list" aria-live="polite"></div>
				<p class="rl-cabinet-head__hint rl-cabinet-head__hint--empty" id="rl-cabinet-tags-hint" hidden>
					<?php esc_html_e('Добавьте теги, чтобы мы подбирали заказы под вас.', 'rawlead-kadence-child'); ?>
				</p>
			</header>
			<header class="rl-feed-head rl-cabinet-feed-head">
				<p class="rl-feed-head__count" id="rl-cabinet-count" aria-live="polite"></p>
				<button type="button" class="rl-btn rl-btn--ghost rl-feed-filters-btn" id="rl-cabinet-filters-open" aria-expanded="false">
					<?php esc_html_e('Фильтры', 'rawlead-kadence-child'); ?>
				</button>
			</header>
			<div class="rl-feed-banner" id="rl-cabinet-error" role="alert" hidden></div>
			<div class="rl-cabinet-empty rl-cabinet-empty--no-tags" id="rl-cabinet-no-tags" hidden>
				<p><?php esc_html_e('Добавьте теги профиля, чтобы видеть персональную ленту.', 'rawlead-kadence-child'); ?></p>
				<button type="button" class="rl-btn rl-btn--primary" id="rl-cabinet-add-first"><?php esc_html_e('Добавить тег', 'rawlead-kadence-child'); ?></button>
			</div>
			<div class="rl-cabinet-empty rl-cabinet-empty--no-match" id="rl-cabinet-no-match" hidden>
				<p><?php esc_html_e('Подходящих заказов пока нет. Попробуйте расширить теги или проверьте позже.', 'rawlead-kadence-child'); ?></p>
				<a class="rl-btn rl-btn--ghost" href="<?php echo esc_url(rawlead_page_url('lenta')); ?>">
					<?php esc_html_e('Смотреть открытую ленту', 'rawlead-kadence-child'); ?>
				</a>
			</div>
			<div class="rl-feed-list" id="rl-cabinet-list" aria-live="polite"></div>
			<div class="rl-feed-sentinel" id="rl-cabinet-sentinel" aria-hidden="true"></div>
			<p class="rl-feed-end" id="rl-cabinet-end" hidden><?php esc_html_e('Все заказы загружены', 'rawlead-kadence-child'); ?></p>
		</div>
	</div>
	<div class="rl-feed-sheet" id="rl-cabinet-sheet" hidden>
		<div class="rl-feed-sheet__overlay" id="rl-cabinet-sheet-overlay"></div>
		<div class="rl-feed-sheet__panel" role="dialog" aria-modal="true" aria-label="<?php esc_attr_e('Фильтры', 'rawlead-kadence-child'); ?>">
			<div class="rl-feed-sheet__body" id="rl-cabinet-sheet-body"></div>
			<div class="rl-feed-sheet__actions">
				<button type="button" class="rl-btn rl-btn--primary" id="rl-cabinet-sheet-apply"><?php esc_html_e('Применить', 'rawlead-kadence-child'); ?></button>
				<button type="button" class="rl-btn rl-btn--ghost" id="rl-cabinet-sheet-reset"><?php esc_html_e('Сбросить', 'rawlead-kadence-child'); ?></button>
			</div>
		</div>
	</div>
</main>
<?php
rawlead_get_part('footer');
get_footer();
