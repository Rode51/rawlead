<?php
/**
 * Quiz onboarding — match-first profile (O209).
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

$rl_quiz_lenta = rawlead_page_url('lenta');
$rl_quiz_cabinet_login = rawlead_cabinet_login_url();
$rl_quiz_overlay = !empty($rl_quiz_overlay);
$rl_quiz_skip_href = $rl_quiz_overlay ? '#' : $rl_quiz_lenta;
$rl_quiz_skip_class = $rl_quiz_overlay ? ' rl-quiz__skip-close js-quiz-overlay-close' : '';
?>
<section class="rl-quiz<?php echo $rl_quiz_overlay ? ' rl-quiz--overlay' : ''; ?>" id="rl-quiz" aria-live="polite">
	<div class="rl-quiz-stage" id="rl-quiz-stage">
		<div class="rl-quiz__intro" id="rl-quiz-intro">
			<div class="rl-quiz__intro-card">
				<p class="rl-quiz__wordmark">RAWLEAD</p>
				<h1 class="rl-quiz__intro-title"><?php esc_html_e('Ответь на карточки — лента найдёт твои заказы', 'rawlead-kadence-child'); ?></h1>
			</div>
			<p class="rl-quiz__intro-sub">
				<?php esc_html_e('Отвечай на заказы — ИИ собирает твой профиль на ходу', 'rawlead-kadence-child'); ?>
			</p>
			<button type="button" class="rl-btn rl-btn--primary rl-quiz__intro-start" id="rl-quiz-intro-start">
				<?php esc_html_e('Начать  →', 'rawlead-kadence-child'); ?>
			</button>
			<p class="rl-quiz__skip rl-quiz__skip--intro">
				<a class="rl-link-muted rl-quiz__skip-link<?php echo esc_attr($rl_quiz_skip_class); ?>" href="<?php echo esc_url($rl_quiz_skip_href); ?>">
					<?php esc_html_e('Смотреть ленту без настройки →', 'rawlead-kadence-child'); ?>
				</a>
			</p>
		</div>
		<div class="rl-quiz__loading" id="rl-quiz-loading" hidden>
			<span class="rl-quiz__spinner" aria-hidden="true"></span>
			<p class="rl-quiz__lead"><?php esc_html_e('Загружаем карточки…', 'rawlead-kadence-child'); ?></p>
		</div>
		<div class="rl-quiz__error" id="rl-quiz-error" role="alert" hidden>
			<p class="rl-quiz__error-text" id="rl-quiz-error-text"></p>
			<button type="button" class="rl-btn rl-btn--ghost" id="rl-quiz-error-retry"><?php esc_html_e('Попробовать', 'rawlead-kadence-child'); ?></button>
			<p class="rl-quiz__skip">
				<a class="rl-link-muted<?php echo esc_attr($rl_quiz_skip_class); ?>" href="<?php echo esc_url($rl_quiz_skip_href); ?>">
					<?php esc_html_e('Смотреть ленту без настройки →', 'rawlead-kadence-child'); ?>
				</a>
			</p>
		</div>
		<div class="rl-quiz__play" id="rl-quiz-play" hidden>
			<header class="rl-quiz__head">
				<div class="rl-quiz__head-row">
					<p class="rl-quiz__progress" id="rl-quiz-progress" aria-live="polite"><?php esc_html_e('Профиль формируется…', 'rawlead-kadence-child'); ?></p>
					<button type="button" class="rl-quiz__restart" id="rl-quiz-restart">
						<?php esc_html_e('Начать сначала', 'rawlead-kadence-child'); ?>
					</button>
				</div>
				<div class="rl-quiz__progress-bar" aria-hidden="true">
					<span class="rl-quiz__progress-fill" id="rl-quiz-progress-fill" style="width:10%"></span>
				</div>
			</header>
			<div class="rl-feed-list rl-quiz-card-stage" id="rl-quiz-card-stage">
				<article class="rl-lead-card is-expanded rl-quiz-feed-card rl-quiz-card" id="rl-quiz-card" hidden>
					<div class="rl-feed-card__head rl-quiz-card__head">
						<span class="rl-feed-card__time" id="rl-quiz-card-time" hidden></span>
						<div class="rl-feed-card__badge-stack" id="rl-quiz-card-source"></div>
					</div>
					<h3 class="rl-lead-card__title"><span id="rl-quiz-card-title"></span></h3>
					<p class="rl-lead-card__budget" id="rl-quiz-card-budget"></p>
					<div class="rl-chips rl-chips--expanded-visible" id="rl-quiz-card-tags"></div>
					<div class="rl-card-cta-zone rl-quiz-card__actions">
						<button type="button" class="rl-card-cta rl-quiz-card__nope" id="rl-quiz-nope">
							<?php esc_html_e('Мимо', 'rawlead-kadence-child'); ?>
						</button>
						<button type="button" class="rl-card-cta rl-card-cta--primary rl-quiz-card__like" id="rl-quiz-like">
							<?php esc_html_e('Берем', 'rawlead-kadence-child'); ?>
						</button>
					</div>
					<div class="rl-feed-card__body">
						<div class="rl-feed-card__body-inner">
							<div class="rl-feed-card__section">
								<h4 class="rl-feed-card__section-title"><?php esc_html_e('Суть задания', 'rawlead-kadence-child'); ?></h4>
								<p class="rl-feed-card__task" id="rl-quiz-card-task"></p>
							</div>
						</div>
					</div>
				</article>
			</div>
			<p class="rl-quiz__early-cta" id="rl-quiz-early-cta" hidden>
				<button type="button" class="rl-link-muted" id="rl-quiz-early-btn">
					<?php esc_html_e('Хватит → смотреть ленту', 'rawlead-kadence-child'); ?>
				</button>
			</p>
		</div>
	</div>
	<div class="rl-quiz__result" id="rl-quiz-result" hidden>
		<h2 class="rl-quiz__result-title" id="rl-quiz-result-title"><?php esc_html_e('Готово. Вот что мы узнали:', 'rawlead-kadence-child'); ?></h2>
		<div class="rl-quiz__category-bars" id="rl-quiz-category-bars" aria-hidden="false"></div>
		<p class="rl-quiz__result-sub" id="rl-quiz-result-sub">
			<?php esc_html_e('Лента уже настраивается. Войди — сохраним профиль и откроем персональную ленту.', 'rawlead-kadence-child'); ?>
		</p>
		<p class="rl-quiz__result-hint" id="rl-quiz-result-hint">
			<?php esc_html_e('Чем больше откликаешься — тем точнее совпадения.', 'rawlead-kadence-child'); ?>
		</p>
		<a class="rl-quiz__cabinet-cta" id="rl-quiz-cabinet-cta" href="<?php echo esc_url($rl_quiz_cabinet_login); ?>" hidden>
			<svg class="rl-quiz__cabinet-cta-icon" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
				<path fill="currentColor" d="M9.04 15.314l-.376 5.302c.538 0 .77-.231 1.049-.508l2.518-2.418 5.217 3.823c.957.527 1.637.251 1.898-.885l3.438-16.08.001-.001c.305-1.423-.514-1.98-1.447-1.634L1.12 9.775c-1.392.541-1.369 1.317-.236 1.667l4.913 1.533L18.9 5.48c.595-.394 1.136-.176.691.218"/>
			</svg>
			<span><?php esc_html_e('3 дня Premium бесплатно — автоматически при входе', 'rawlead-kadence-child'); ?></span>
		</a>
		<div class="rl-quiz__login" id="rl-quiz-login" hidden>
			<div id="rl-quiz-telegram-widget"></div>
			<p class="rl-quiz__login-state" id="rl-quiz-login-state" aria-live="polite" hidden></p>
		</div>
		<p class="rl-quiz__open-lenta" id="rl-quiz-open-lenta" hidden>
			<?php if ($rl_quiz_overlay) : ?>
				<button type="button" class="rl-btn rl-btn--primary js-quiz-overlay-close">
					<?php esc_html_e('Открыть ленту →', 'rawlead-kadence-child'); ?>
				</button>
			<?php else : ?>
				<a class="rl-btn rl-btn--primary" href="<?php echo esc_url($rl_quiz_lenta); ?>">
					<?php esc_html_e('Открыть ленту →', 'rawlead-kadence-child'); ?>
				</a>
			<?php endif; ?>
		</p>
		<p class="rl-quiz__retry" id="rl-quiz-retry" hidden>
			<button type="button" class="rl-btn rl-btn--ghost"><?php esc_html_e('Начать заново', 'rawlead-kadence-child'); ?></button>
		</p>
		<p class="rl-quiz__skip" id="rl-quiz-skip-result">
			<a class="rl-link-muted<?php echo esc_attr($rl_quiz_skip_class); ?>" href="<?php echo esc_url($rl_quiz_skip_href); ?>">
				<?php esc_html_e('Смотреть без входа →', 'rawlead-kadence-child'); ?>
			</a>
		</p>
	</div>
</section>
