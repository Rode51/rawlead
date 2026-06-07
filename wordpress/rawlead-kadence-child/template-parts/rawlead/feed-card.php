<?php
/**
 * Lead Card v3 — tier helper (O127). Cards render in rawlead-feed.js.
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

/**
 * Feed tier for filter bar + card data-tier (JS may upgrade free → premium).
 */
function rawlead_feed_tier(bool $logged_in = false): string {
    if (!$logged_in) {
        return 'anon';
    }
    return 'free';
}
