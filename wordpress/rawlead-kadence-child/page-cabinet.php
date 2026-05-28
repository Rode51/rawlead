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
<?php
$rawlead_cabinet_is_local = rawlead_is_local_dev();
$rawlead_cabinet_login_url = rawlead_cabinet_login_url();
?>
<main id="primary" class="rl-app rl-app--cabinet rl-cabinet--gate site-main" data-rl-app="cabinet">
	<section class="rl-cabinet-login" id="rl-cabinet-login">
		<div class="rl-cabinet-login__card">
			<h1 class="rl-cabinet-login__title"><?php esc_html_e('Кабинет', 'rawlead-kadence-child'); ?></h1>
			<p class="rl-cabinet-login__lead"><?php esc_html_e('Вход через Telegram = ваш аккаунт. Навыки в профиле, отклики — в inbox.', 'rawlead-kadence-child'); ?></p>
			<div id="rl-telegram-login-widget" class="rl-cabinet-login__widget"></div>
			<p class="rl-cabinet-login__state rl-cabinet-login__state--info" id="rl-cabinet-login-state" aria-live="polite"></p>
			<p class="rl-cabinet-login__hint" id="rl-cabinet-login-hint" hidden></p>
			<?php if ($rawlead_cabinet_is_local) : ?>
			<p class="rl-cabinet-login__hint">
				<?php esc_html_e('Если видите серый/битый блок вместо кнопки Telegram — браузер не открывает telegram.org. Откройте кабинет на 127.0.0.1 и включите VPN/прокси или отключите блокировщик для telegram.org.', 'rawlead-kadence-child'); ?>
			</p>
			<?php else : ?>
			<p class="rl-cabinet-login__hint">
				<?php esc_html_e('Из РФ для входа нужен VPN (Telegram заблокирован). Если кнопка не загрузилась — используйте «Войти через Telegram» ниже.', 'rawlead-kadence-child'); ?>
			</p>
			<?php endif; ?>
			<div class="rl-cabinet-login__fallback" id="rl-cabinet-login-fallback" hidden>
				<p class="rl-cabinet-login__hint"><?php esc_html_e('Вход без iframe: нажмите кнопку — откроется Telegram OAuth и вернёт в /cabinet/.', 'rawlead-kadence-child'); ?></p>
				<p class="rl-cabinet-login__direct">
					<a class="rl-btn rl-btn--primary" id="rl-cabinet-fallback-link" href="#">
						<?php esc_html_e('Войти через Telegram (fallback)', 'rawlead-kadence-child'); ?>
					</a>
				</p>
			</div>
			<?php if ($rawlead_cabinet_is_local) : ?>
			<p class="rl-cabinet-login__direct">
				<a class="rl-btn rl-btn--ghost" href="<?php echo esc_url($rawlead_cabinet_login_url); ?>">
					<?php esc_html_e('Открыть по адресу для Telegram (127.0.0.1)', 'rawlead-kadence-child'); ?>
				</a>
			</p>
			<?php endif; ?>
			<p class="rl-cabinet-login__bot-hint">
				<?php
				printf(
					/* translators: %s: Telegram bot username */
					esc_html__('Чтобы получать match-лиды в Telegram — %1$s/start%2$s в боте @rawlead_bot. Отклики пишите на %3$sленте%4$s.', 'rawlead-kadence-child'),
					'<code>',
					'</code>',
					'<a href="' . esc_url(rawlead_page_url('lenta')) . '">',
					'</a>'
				);
				?>
			</p>
			<p class="rl-cabinet-login__direct">
				<a class="rl-btn rl-btn--ghost" href="https://t.me/rawlead_bot" target="_blank" rel="noopener">
					<?php esc_html_e('Открыть @rawlead_bot', 'rawlead-kadence-child'); ?>
				</a>
			</p>
		</div>
	</section>
	<div class="rl-container rl-app__layout rl-cabinet-app" id="rl-cabinet-app" hidden>
		<div class="rl-cabinet-user" id="rl-cabinet-user" hidden>
			<img class="rl-cabinet-user__avatar" id="rl-cabinet-user-avatar" alt="" width="40" height="40" hidden>
			<div class="rl-cabinet-user__info">
				<p class="rl-cabinet-user__label">
					<?php esc_html_e('Вы вошли как', 'rawlead-kadence-child'); ?>
					<strong id="rl-cabinet-user-name"></strong>
				</p>
				<p class="rl-cabinet-user__hint">
					<a href="https://t.me/rawlead_bot" target="_blank" rel="noopener"><?php esc_html_e('Открыть @rawlead_bot', 'rawlead-kadence-child'); ?></a>
					<?php esc_html_e('· /start — push match-лидов', 'rawlead-kadence-child'); ?>
				</p>
			</div>
			<button type="button" class="rl-btn rl-btn--ghost" id="rl-cabinet-logout"><?php esc_html_e('Выйти', 'rawlead-kadence-child'); ?></button>
		</div>
		<section class="rl-cabinet-sub" id="rl-cabinet-sub" aria-labelledby="rl-cabinet-sub-title" hidden>
			<div class="rl-cabinet-sub__head">
				<h2 class="rl-cabinet-sub__title" id="rl-cabinet-sub-title"><?php esc_html_e('Подписка', 'rawlead-kadence-child'); ?></h2>
				<span class="rl-cabinet-sub__badge" id="rl-cabinet-sub-badge" aria-live="polite"></span>
			</div>
			<p class="rl-cabinet-sub__plan" id="rl-cabinet-sub-plan"></p>
			<p class="rl-cabinet-sub__detail" id="rl-cabinet-sub-detail"></p>
			<div class="rl-cabinet-sub__actions">
				<a class="rl-btn rl-btn--primary rl-cabinet-sub__pay" id="rl-cabinet-sub-pay" href="<?php echo esc_url(rawlead_page_url('pricing')); ?>">
					<?php esc_html_e('Оплатить Stars — скоро', 'rawlead-kadence-child'); ?>
				</a>
				<button type="button" class="rl-btn rl-btn--ghost rl-cabinet-sub__pause" id="rl-cabinet-sub-pause" hidden disabled>
					<?php esc_html_e('Поставить на паузу', 'rawlead-kadence-child'); ?>
				</button>
				<button type="button" class="rl-btn rl-btn--ghost rl-cabinet-sub__resume" id="rl-cabinet-sub-resume" hidden>
					<?php esc_html_e('Возобновить', 'rawlead-kadence-child'); ?>
				</button>
			</div>
			<p class="rl-cabinet-sub__note" id="rl-cabinet-sub-note">
				<?php esc_html_e('Сейчас лента и кабинет бесплатны в режиме beta. Оплата через Telegram Stars подключится в следующем релизе.', 'rawlead-kadence-child'); ?>
			</p>
		</section>
		<section class="rl-cabinet-notif" id="rl-cabinet-notif" aria-labelledby="rl-cabinet-notif-title" hidden>
			<h2 class="rl-cabinet-notif__title" id="rl-cabinet-notif-title"><?php esc_html_e('Уведомления', 'rawlead-kadence-child'); ?></h2>
			<div class="rl-cabinet-notif__row">
				<label class="rl-cabinet-notif__label" for="rl-cabinet-notif-threshold"><?php esc_html_e('Уведомлять от % совпадения:', 'rawlead-kadence-child'); ?></label>
				<select class="rl-cabinet-notif__select" id="rl-cabinet-notif-threshold" aria-label="<?php esc_attr_e('Порог совпадения для push', 'rawlead-kadence-child'); ?>">
					<option value="30">30%</option>
					<option value="40">40%</option>
					<option value="50">50%</option>
					<option value="60" selected>60%</option>
					<option value="70">70%</option>
					<option value="80">80%</option>
					<option value="90">90%</option>
					<option value="100">100%</option>
				</select>
			</div>
			<div class="rl-cabinet-notif__row rl-cabinet-notif__row--toggle">
				<label class="rl-cabinet-notif__label" for="rl-cabinet-notif-enabled"><?php esc_html_e('Push в Telegram', 'rawlead-kadence-child'); ?></label>
				<button type="button" class="rl-toggle" id="rl-cabinet-notif-enabled" role="switch" aria-checked="true">
					<span class="rl-toggle__knob"></span>
				</button>
			</div>
			<p class="rl-cabinet-notif__status" id="rl-cabinet-notif-status" aria-live="polite"></p>
		</section>
		<div class="rl-feed-main rl-cabinet-inbox">
			<header class="rl-cabinet-head">
				<h1 class="rl-cabinet-head__title"><?php esc_html_e('Мои отклики', 'rawlead-kadence-child'); ?></h1>
				<p class="rl-cabinet-head__lead"><?php esc_html_e('Заказы, где вы нажали «Написать отклик» на ленте. Ленту заказов смотрите на /lenta/.', 'rawlead-kadence-child'); ?></p>
				<p class="rl-cabinet-head__label"><?php esc_html_e('Ваши навыки:', 'rawlead-kadence-child'); ?></p>
				<div class="rl-cabinet-tags" id="rl-cabinet-tags" role="list" aria-live="polite"></div>
				<button type="button" class="rl-btn rl-btn--ghost rl-cabinet-tags-clear" id="rl-cabinet-tags-clear" hidden><?php esc_html_e('Очистить теги', 'rawlead-kadence-child'); ?></button>
				<p class="rl-cabinet-head__hint rl-cabinet-head__hint--empty" id="rl-cabinet-tags-hint" hidden>
					<?php esc_html_e('Добавьте навыки — на ленте точнее подберём заказы и отклики', 'rawlead-kadence-child'); ?>
				</p>
			</header>
			<header class="rl-feed-head rl-cabinet-feed-head">
				<p class="rl-feed-head__count" id="rl-cabinet-count" aria-live="polite"></p>
			</header>
			<div class="rl-feed-banner" id="rl-cabinet-error" role="alert" hidden></div>
			<div class="rl-cabinet-empty rl-cabinet-empty--no-tags" id="rl-cabinet-no-tags" hidden>
				<p><?php esc_html_e('Добавьте навыки — на ленте точнее подберём заказы', 'rawlead-kadence-child'); ?></p>
				<button type="button" class="rl-btn rl-btn--primary" id="rl-cabinet-add-first"><?php esc_html_e('Добавить навык', 'rawlead-kadence-child'); ?></button>
			</div>
			<div class="rl-cabinet-empty rl-cabinet-empty--no-match" id="rl-cabinet-no-match" hidden>
				<p><?php esc_html_e('Пока нет откликов. На ленте нажмите «Написать отклик» у подходящего заказа.', 'rawlead-kadence-child'); ?></p>
				<a class="rl-btn rl-btn--primary" href="<?php echo esc_url(rawlead_page_url('lenta')); ?>"><?php esc_html_e('Открыть ленту', 'rawlead-kadence-child'); ?></a>
			</div>
			<div class="rl-feed-list" id="rl-cabinet-list" aria-live="polite"></div>
			<div class="rl-feed-sentinel" id="rl-cabinet-sentinel" aria-hidden="true"></div>
			<p class="rl-feed-end" id="rl-cabinet-end" hidden><?php esc_html_e('Все заказы показаны', 'rawlead-kadence-child'); ?></p>
		</div>
	</div>
	<div class="rl-cabinet-skills-modal" id="rl-cabinet-skills-modal" hidden>
		<div class="rl-cabinet-skills-modal__overlay" id="rl-cabinet-skills-modal-overlay"></div>
		<div class="rl-skills-panel rl-cabinet-skills-modal__panel" role="dialog" aria-modal="true" aria-labelledby="rl-cabinet-skills-title">
			<h3 class="rl-skills-panel__title" id="rl-cabinet-skills-title"><?php esc_html_e('Выбрать специализацию', 'rawlead-kadence-child'); ?></h3>
			<label class="rl-cabinet-skills-search-wrap">
				<span class="screen-reader-text"><?php esc_html_e('Поиск навыка', 'rawlead-kadence-child'); ?></span>
				<input type="search" class="rl-cabinet-skills-search" id="rl-cabinet-skills-search" placeholder="<?php esc_attr_e('Поиск навыка…', 'rawlead-kadence-child'); ?>" autocomplete="off">
			</label>
			<div class="rl-skills-panel__body">
				<div class="rl-feed-skills" id="rl-cabinet-skills-catalog" aria-live="polite"></div>
				<button type="button" class="rl-feed-skills-rare" id="rl-cabinet-skills-rare" hidden><?php esc_html_e('Ещё навыки', 'rawlead-kadence-child'); ?></button>
				<p class="rl-feed-skills__hint" id="rl-cabinet-skills-limit" hidden><?php esc_html_e('Максимум 6 навыков', 'rawlead-kadence-child'); ?></p>
			</div>
			<div class="rl-skills-panel__footer">
				<button type="button" class="rl-btn rl-btn--primary rl-feed-skills-apply" id="rl-cabinet-skills-apply"><?php esc_html_e('Добавить', 'rawlead-kadence-child'); ?></button>
				<button type="button" class="rl-btn rl-btn--ghost" id="rl-cabinet-skills-cancel"><?php esc_html_e('Отмена', 'rawlead-kadence-child'); ?></button>
			</div>
		</div>
	</div>
</main>
<?php
rawlead_get_part('footer');
get_footer();
