<?php

/**

 * RawLead API — единый URL бэкенда + REST-прокси для WP (same-origin).

 *

 * Переопределение: define('RAWLEAD_API_URL', 'http://127.0.0.1:18766'); в wp-config.php

 *

 * @package RawLead_Kadence_Child

 */



declare(strict_types=1);



if (!defined('ABSPATH')) {

    exit;

}



/** MVP owner user (#1) — см. pg_storage._OWNER_USER_ID */

const RAWLEAD_OWNER_USER_ID = '00000000-0000-0000-0000-000000000001';



/** Базовый URL FastAPI (без завершающего слэша). */

function rawlead_api_base_url(): string {

    if (defined('RAWLEAD_API_URL')) {

        return rtrim((string) RAWLEAD_API_URL, '/');

    }
    $host = strtolower((string) wp_parse_url(home_url('/'), PHP_URL_HOST));
    if (in_array($host, ['rawlead.ru', 'www.rawlead.ru'], true)) {
        return 'https://api.rawlead.ru';
    }

    return 'http://127.0.0.1:18766';

}



/** @return array<string, string> */

function rawlead_api_owner_headers(): array {

    return [

        'Accept'              => 'application/json',

        'X-RawLead-User-Id'   => RAWLEAD_OWNER_USER_ID,

    ];

}



/** @username бота для Telegram Login Widget (wp-config: RAWLEAD_TG_BOT_USERNAME). */

function rawlead_tg_login_bot_username(): string {

    if (defined('RAWLEAD_TG_BOT_USERNAME')) {

        $value = trim((string) RAWLEAD_TG_BOT_USERNAME);
        $normalized = ltrim(strtolower($value), '@');
        if ($normalized === 'rawlead_bot') {
            return 'rawlead_bot';
        }

    }

    return 'rawlead_bot';

}



/** Bearer из REST-запроса браузера. */

function rawlead_api_bearer_from_request(WP_REST_Request $request): string {

    $auth = $request->get_header('authorization');

    if (is_string($auth) && $auth !== '' && stripos($auth, 'Bearer ') === 0) {

        $token = trim(substr($auth, 7));

        if ($token !== '') {

            return $token;

        }

    }

    $cookie = isset($_COOKIE['rl_access']) ? trim((string) $_COOKIE['rl_access']) : '';

    return $cookie;

}



/**

 * @return string|WP_Error PNG bytes

 */

function rawlead_fetch_qr_png(string $data) {

    $data = trim($data);

    if ($data === '' || strlen($data) > 2000) {

        return new WP_Error('rawlead_invalid', 'invalid qr data', ['status' => 400]);

    }



    $url = 'https://api.qrserver.com/v1/create-qr-code/?size=260x260&margin=12&format=png&data=' . rawurlencode($data);

    $response = wp_remote_get($url, ['timeout' => 12]);



    if (is_wp_error($response)) {

        return $response;

    }



    $code = (int) wp_remote_retrieve_response_code($response);

    $body = wp_remote_retrieve_body($response);

    if ($code < 200 || $code >= 300 || $body === '') {

        return new WP_Error('rawlead_qr', 'qr fetch failed', ['status' => 502]);

    }



    return $body;

}



/**

 * @return array<string, string>

 */

function rawlead_api_user_headers(WP_REST_Request $request, bool $owner_fallback = false): array {

    $headers = ['Accept' => 'application/json'];

    $bearer = rawlead_api_bearer_from_request($request);

    if ($bearer !== '') {

        $headers['Authorization'] = 'Bearer ' . $bearer;

        return $headers;

    }

    if ($owner_fallback) {

        return rawlead_api_owner_headers();

    }

    return $headers;

}



/**

 * @param array<string, scalar> $query

 * @return array<string, mixed>|WP_Error

 */

function rawlead_api_get(string $path, array $query = [], bool $owner = false, ?WP_REST_Request $request = null): array|WP_Error {

    $url = rawlead_api_base_url() . $path;

    if ($query !== []) {

        $url .= '?' . http_build_query($query);

    }



    $headers = ['Accept' => 'application/json'];

    if ($owner) {

        $headers = rawlead_api_owner_headers();

    } elseif ($request instanceof WP_REST_Request) {

        $bearer = rawlead_api_bearer_from_request($request);

        if ($bearer !== '') {

            $headers['Authorization'] = 'Bearer ' . $bearer;

        }

    }



    $response = wp_remote_get($url, [

        'timeout' => 20,

        'headers' => $headers,

    ]);



    if (is_wp_error($response)) {

        return $response;

    }



    $code = (int) wp_remote_retrieve_response_code($response);

    $body = wp_remote_retrieve_body($response);

    $data = json_decode($body, true);



    if ($code < 200 || $code >= 300) {

        $detail = is_array($data) && isset($data['detail']) ? (string) $data['detail'] : $body;

        return new WP_Error('rawlead_api_http', $detail ?: 'API error', ['status' => $code]);

    }



    return is_array($data) ? $data : [];

}



/**

 * @param array<string, mixed> $body

 * @return array<string, mixed>|WP_Error

 */

function rawlead_api_put(string $path, array $body, bool $owner = false): array|WP_Error {

    $url = rawlead_api_base_url() . $path;

    $headers = [

        'Accept'       => 'application/json',

        'Content-Type' => 'application/json',

    ];

    if ($owner) {

        $headers = array_merge($headers, rawlead_api_owner_headers());

    }



    $response = wp_remote_request($url, [

        'method'  => 'PUT',

        'timeout' => 20,

        'headers' => $headers,

        'body'    => wp_json_encode($body),

    ]);



    if (is_wp_error($response)) {

        return $response;

    }



    $code = (int) wp_remote_retrieve_response_code($response);

    $raw = wp_remote_retrieve_body($response);

    $data = json_decode($raw, true);



    if ($code < 200 || $code >= 300) {

        $detail = is_array($data) && isset($data['detail']) ? (string) $data['detail'] : $raw;

        return new WP_Error('rawlead_api_http', $detail ?: 'API error', ['status' => $code]);

    }



    return is_array($data) ? $data : [];

}



/**

 * @param array<string, mixed> $body

 * @return array<string, mixed>|WP_Error

 */

function rawlead_api_post(string $path, array $body, array $extra_headers = []): array|WP_Error {

    $url = rawlead_api_base_url() . $path;

    $headers = array_merge(

        [

            'Accept'       => 'application/json',

            'Content-Type' => 'application/json',

        ],

        $extra_headers

    );



    $response = wp_remote_post($url, [

        'timeout' => 20,

        'headers' => $headers,

        'body'    => wp_json_encode($body),

    ]);



    if (is_wp_error($response)) {

        return $response;

    }



    $code = (int) wp_remote_retrieve_response_code($response);

    $raw = wp_remote_retrieve_body($response);

    $data = json_decode($raw, true);



    if ($code < 200 || $code >= 300) {

        $detail = is_array($data) && isset($data['detail']) ? (string) $data['detail'] : $raw;

        return new WP_Error('rawlead_api_http', $detail ?: 'API error', ['status' => $code]);

    }



    return is_array($data) ? $data : [];

}



add_action('rest_api_init', static function (): void {

    register_rest_route('rawlead/v1', '/auth/telegram', [

        'methods'             => 'POST',

        'permission_callback' => '__return_true',

        'callback'            => static function (WP_REST_Request $request): WP_REST_Response|WP_Error {

            $body = $request->get_json_params();

            if (!is_array($body)) {

                return new WP_Error('rawlead_invalid', 'Expected JSON body', ['status' => 400]);

            }

            $data = rawlead_api_post('/v1/auth/telegram', $body);

            if (is_wp_error($data)) {

                return $data;

            }

            return new WP_REST_Response($data, 200);

        },

    ]);

    register_rest_route('rawlead/v1', '/auth/bot-session', [

        'methods'             => 'POST',

        'permission_callback' => '__return_true',

        'callback'            => static function (): WP_REST_Response|WP_Error {

            $data = rawlead_api_post('/v1/auth/bot-session', []);

            if (is_wp_error($data)) {

                return $data;

            }

            return new WP_REST_Response($data, 200);

        },

    ]);

    register_rest_route('rawlead/v1', '/auth/qr-image', [

        'methods'             => 'GET',

        'permission_callback' => '__return_true',

        'args'                => [

            'data' => [

                'type'              => 'string',

                'required'          => true,

                'sanitize_callback' => static function ($value): string {

                    return is_string($value) ? trim($value) : '';

                },

            ],

        ],

        'callback'            => static function (WP_REST_Request $request): WP_REST_Response|WP_Error {

            $png = rawlead_fetch_qr_png((string) $request->get_param('data'));

            if (is_wp_error($png)) {

                return $png;

            }

            $response = new WP_REST_Response($png, 200);

            $response->header('Content-Type', 'image/png');

            $response->header('Cache-Control', 'private, max-age=300');

            return $response;

        },

    ]);

    register_rest_route('rawlead/v1', '/auth/bot-complete', [

        'methods'             => ['GET', 'POST'],

        'permission_callback' => '__return_true',

        'callback'            => static function (WP_REST_Request $request): WP_REST_Response|WP_Error {

            if ($request->get_method() === 'GET') {

                $auth = trim((string) $request->get_param('auth'));

                if ($auth === '') {

                    return new WP_Error('rawlead_invalid', 'auth required', ['status' => 400]);

                }

                $data = rawlead_api_get('/v1/auth/bot-complete', ['auth' => $auth]);

                if (is_wp_error($data)) {

                    return $data;

                }

                return new WP_REST_Response($data, 200);

            }

            $body = $request->get_json_params();

            if (!is_array($body)) {

                return new WP_Error('rawlead_invalid', 'Expected JSON body', ['status' => 400]);

            }

            $data = rawlead_api_post('/v1/auth/bot-complete', $body);

            if (is_wp_error($data)) {

                return $data;

            }

            return new WP_REST_Response($data, 200);

        },

    ]);

    register_rest_route('rawlead/v1', '/admin/pageview', [

        'methods'             => 'POST',

        'permission_callback' => '__return_true',

        'callback'            => static function (WP_REST_Request $request): WP_REST_Response|WP_Error {

            $body = $request->get_json_params();

            if (!is_array($body)) {

                return new WP_Error('rawlead_invalid', 'Expected JSON body', ['status' => 400]);

            }

            $data = rawlead_api_post('/v1/admin/pageview', $body);

            if (is_wp_error($data)) {

                return $data;

            }

            return new WP_REST_Response(null, 204);

        },

    ]);

    register_rest_route('rawlead/v1', '/ops/dashboard', [

        'methods'             => 'GET',

        'permission_callback' => '__return_true',

        'callback'            => static function (WP_REST_Request $request): WP_REST_Response|WP_Error {

            $data = rawlead_api_get('/v1/admin/dashboard', [], false, $request);

            if (is_wp_error($data)) {

                return $data;

            }

            return new WP_REST_Response($data, 200);

        },

    ]);

    register_rest_route('rawlead/v1', '/ops/leads/(?P<id>\d+)/hide', [

        'methods'             => 'POST',

        'permission_callback' => '__return_true',

        'callback'            => static function (WP_REST_Request $request): WP_REST_Response|WP_Error {

            $id = (int) $request['id'];

            if ($id <= 0) {

                return new WP_Error('rawlead_invalid', 'invalid lead id', ['status' => 400]);

            }

            $bearer = rawlead_api_bearer_from_request($request);

            $headers = $bearer !== '' ? ['Authorization' => 'Bearer ' . $bearer] : [];

            $data = rawlead_api_post('/v1/admin/leads/' . $id . '/hide', [], $headers);

            if (is_wp_error($data)) {

                return $data;

            }

            return new WP_REST_Response($data, 200);

        },

    ]);

    register_rest_route('rawlead/v1', '/ops/control', [
        'methods'             => 'POST',
        'permission_callback' => '__return_true',
        'callback'            => static function (WP_REST_Request $request): WP_REST_Response|WP_Error {
            $body = $request->get_json_params();
            if (!is_array($body)) {
                return new WP_Error('rawlead_invalid', 'Expected JSON body', ['status' => 400]);
            }
            $bearer = rawlead_api_bearer_from_request($request);
            $headers = $bearer !== '' ? ['Authorization' => 'Bearer ' . $bearer] : [];
            $data = rawlead_api_post('/v1/admin/control', $body, $headers);
            if (is_wp_error($data)) {
                return $data;
            }
            return new WP_REST_Response($data, 200);
        },
    ]);




    register_rest_route('rawlead/v1', '/feed', [

        'methods'             => 'GET',

        'permission_callback' => '__return_true',

        'args'                => [

            'limit'     => ['type' => 'integer', 'default' => 20, 'minimum' => 1, 'maximum' => 100],

            'offset'    => ['type' => 'integer', 'default' => 0, 'minimum' => 0],

            'min_score' => ['type' => 'integer', 'default' => 0, 'minimum' => 0, 'maximum' => 100],

            'skills'    => ['type' => 'string', 'default' => ''],

            'category'  => ['type' => 'string', 'default' => ''],

            'sort'      => ['type' => 'string', 'default' => 'time'],

        ],

        'callback'            => static function (WP_REST_Request $request): WP_REST_Response|WP_Error {

            $query = [

                'limit'     => (int) $request->get_param('limit'),

                'offset'    => (int) $request->get_param('offset'),

                'min_score' => (int) $request->get_param('min_score'),

                'sort'      => (string) $request->get_param('sort'),

            ];

            $skills = trim((string) $request->get_param('skills'));

            if ($skills !== '') {

                $query['skills'] = $skills;

            }

            $category = trim((string) $request->get_param('category'));

            if ($category !== '') {

                $query['category'] = $category;

            }

            $data = rawlead_api_get('/v1/feed', $query, false, $request);

            if (is_wp_error($data)) {

                return $data;

            }

            return new WP_REST_Response($data, 200);

        },

    ]);



    register_rest_route('rawlead/v1', '/leads/(?P<id>\d+)', [

        'methods'             => 'GET',

        'permission_callback' => '__return_true',

        'args'                => [

            'id' => ['type' => 'integer', 'required' => true],

        ],

        'callback'            => static function (WP_REST_Request $request): WP_REST_Response|WP_Error {

            $id = (int) $request->get_param('id');

            $data = rawlead_api_get('/v1/leads/' . $id);

            if (is_wp_error($data)) {

                return $data;

            }

            return new WP_REST_Response($data, 200);

        },

    ]);



    register_rest_route('rawlead/v1', '/skills/catalog', [

        'methods'             => 'GET',

        'permission_callback' => '__return_true',

        'callback'            => static function (WP_REST_Request $request): WP_REST_Response|WP_Error {

            $query = [];

            $category = trim((string) $request->get_param('category'));

            if ($category !== '') {

                $query['category'] = $category;

            }

            $mode = trim((string) $request->get_param('mode'));

            if ($mode !== '') {

                $query['mode'] = $mode;

            }

            $limit = (int) $request->get_param('limit');

            if ($limit > 0) {

                $query['limit'] = $limit;

            }

            $days = (int) $request->get_param('days');

            if ($days > 0) {

                $query['days'] = $days;

            }

            $data = rawlead_api_get('/v1/skills/catalog', $query);

            if (is_wp_error($data)) {

                return $data;

            }

            return new WP_REST_Response($data, 200);

        },

    ]);



    register_rest_route('rawlead/v1', '/me/feed', [

        'methods'             => 'GET',

        'permission_callback' => '__return_true',

        'args'                => [

            'limit'     => ['type' => 'integer', 'default' => 20, 'minimum' => 1, 'maximum' => 100],

            'offset'    => ['type' => 'integer', 'default' => 0, 'minimum' => 0],

            'min_score' => ['type' => 'integer', 'default' => 0, 'minimum' => 0, 'maximum' => 100],

            'min_match' => ['type' => 'integer', 'default' => 0, 'minimum' => 0, 'maximum' => 100],

            'skills'    => ['type' => 'string', 'default' => ''],

            'sort'      => ['type' => 'string', 'default' => 'match'],

        ],

        'callback'            => static function (WP_REST_Request $request): WP_REST_Response|WP_Error {

            if (rawlead_api_bearer_from_request($request) === '') {

                return new WP_Error('rawlead_auth', 'Login required', ['status' => 401]);

            }

            $query = [

                'limit'     => (int) $request->get_param('limit'),

                'offset'    => (int) $request->get_param('offset'),

                'min_score' => (int) $request->get_param('min_score'),

                'min_match' => (int) $request->get_param('min_match'),

                'sort'      => (string) $request->get_param('sort'),

            ];

            $skills = trim((string) $request->get_param('skills'));

            if ($skills !== '') {

                $query['skills'] = $skills;

            }

            $category = trim((string) $request->get_param('category'));

            if ($category !== '') {

                $query['category'] = $category;

            }

            $url = rawlead_api_base_url() . '/v1/me/feed';

            if ($query !== []) {

                $url .= '?' . http_build_query($query);

            }

            $response = wp_remote_get($url, [

                'timeout' => 20,

                'headers' => rawlead_api_user_headers($request, false),

            ]);

            if (is_wp_error($response)) {

                return $response;

            }

            $code = (int) wp_remote_retrieve_response_code($response);

            $raw = wp_remote_retrieve_body($response);

            $data = json_decode($raw, true);

            if ($code < 200 || $code >= 300) {

                $detail = is_array($data) && isset($data['detail']) ? (string) $data['detail'] : $raw;

                return new WP_Error('rawlead_api_http', $detail ?: 'API error', ['status' => $code]);

            }

            $data = is_array($data) ? $data : [];

            if (is_wp_error($data)) {

                return $data;

            }

            return new WP_REST_Response($data, 200);

        },

    ]);



    $draft_route_args = [

        'lead_id' => ['type' => 'integer', 'required' => true, 'minimum' => 1],

    ];

    $draft_proxy = static function (WP_REST_Request $request, string $method): WP_REST_Response|WP_Error {

        if (rawlead_api_bearer_from_request($request) === '') {

            return new WP_Error('rawlead_auth', 'Login required', ['status' => 401]);

        }

        $lead_id = (int) $request->get_param('lead_id');

        $url = rawlead_api_base_url() . '/v1/me/leads/' . $lead_id . '/draft';

        $headers = rawlead_api_user_headers($request, false);

        $timeout = $method === 'POST' ? 90 : 20;

        if ($method === 'POST') {

            $response = wp_remote_post($url, [

                'timeout' => $timeout,

                'headers' => $headers,

            ]);

        } else {

            $response = wp_remote_get($url, [

                'timeout' => $timeout,

                'headers' => $headers,

            ]);

        }

        if (is_wp_error($response)) {

            return $response;

        }

        $code = (int) wp_remote_retrieve_response_code($response);

        $raw = wp_remote_retrieve_body($response);

        $data = json_decode($raw, true);

        if ($code < 200 || $code >= 300) {

            $detail = '';

            $retry_after = null;

            if (is_array($data)) {

                if (isset($data['detail'])) {

                    if (is_string($data['detail'])) {

                        $detail = $data['detail'];

                    } elseif (is_array($data['detail'])) {

                        $detail = (string) ($data['detail']['detail'] ?? 'API error');

                        $retry_after = $data['detail']['retry_after_sec'] ?? null;

                    }

                }

                if ($retry_after === null && isset($data['retry_after_sec'])) {

                    $retry_after = $data['retry_after_sec'];

                }

            }

            if ($detail === '' && is_string($raw) && $raw !== '') {

                $detail = $raw;

            }

            $err_data = ['status' => $code];

            if ($retry_after !== null) {

                $err_data['retry_after_sec'] = (int) $retry_after;

            }

            return new WP_Error('rawlead_api_http', $detail ?: 'API error', $err_data);

        }

        $data = is_array($data) ? $data : [];

        return new WP_REST_Response($data, $code);

    };

    register_rest_route('rawlead/v1', '/me/leads/(?P<lead_id>\d+)/draft', [

        [

            'methods'             => 'GET',

            'permission_callback' => '__return_true',

            'args'                => $draft_route_args,

            'callback'            => static function (WP_REST_Request $request) use ($draft_proxy): WP_REST_Response|WP_Error {

                return $draft_proxy($request, 'GET');

            },

        ],

        [

            'methods'             => 'POST',

            'permission_callback' => '__return_true',

            'args'                => $draft_route_args,

            'callback'            => static function (WP_REST_Request $request) use ($draft_proxy): WP_REST_Response|WP_Error {

                return $draft_proxy($request, 'POST');

            },

        ],

    ]);



    register_rest_route('rawlead/v1', '/me/replies', [

        'methods'             => 'GET',

        'permission_callback' => '__return_true',

        'args'                => [

            'limit'  => ['type' => 'integer', 'default' => 20, 'minimum' => 1, 'maximum' => 100],

            'offset' => ['type' => 'integer', 'default' => 0, 'minimum' => 0],

        ],

        'callback'            => static function (WP_REST_Request $request): WP_REST_Response|WP_Error {

            if (rawlead_api_bearer_from_request($request) === '') {

                return new WP_Error('rawlead_auth', 'Login required', ['status' => 401]);

            }

            $query = [

                'limit'  => (int) $request->get_param('limit'),

                'offset' => (int) $request->get_param('offset'),

            ];

            $url = rawlead_api_base_url() . '/v1/me/replies?' . http_build_query($query);

            $response = wp_remote_get($url, [

                'timeout' => 20,

                'headers' => rawlead_api_user_headers($request, false),

            ]);

            if (is_wp_error($response)) {

                return $response;

            }

            $code = (int) wp_remote_retrieve_response_code($response);

            $raw = wp_remote_retrieve_body($response);

            $data = json_decode($raw, true);

            if ($code < 200 || $code >= 300) {

                $detail = is_array($data) && isset($data['detail']) ? (string) $data['detail'] : $raw;

                return new WP_Error('rawlead_api_http', $detail ?: 'API error', ['status' => $code]);

            }

            return new WP_REST_Response(is_array($data) ? $data : [], 200);

        },

    ]);



    register_rest_route('rawlead/v1', '/me/replies/(?P<lead_id>\d+)', [

        'methods'             => 'DELETE',

        'permission_callback' => '__return_true',

        'args'                => [

            'lead_id' => ['type' => 'integer', 'required' => true, 'minimum' => 1],

        ],

        'callback'            => static function (WP_REST_Request $request): WP_REST_Response|WP_Error {

            if (rawlead_api_bearer_from_request($request) === '') {

                return new WP_Error('rawlead_auth', 'Login required', ['status' => 401]);

            }

            $lead_id = (int) $request->get_param('lead_id');

            $url = rawlead_api_base_url() . '/v1/me/replies/' . $lead_id;

            $response = wp_remote_request($url, [

                'method'  => 'DELETE',

                'timeout' => 20,

                'headers' => rawlead_api_user_headers($request, false),

            ]);

            if (is_wp_error($response)) {

                return $response;

            }

            $code = (int) wp_remote_retrieve_response_code($response);

            $raw = wp_remote_retrieve_body($response);

            $data = json_decode($raw, true);

            if ($code < 200 || $code >= 300) {

                $detail = is_array($data) && isset($data['detail']) ? (string) $data['detail'] : $raw;

                return new WP_Error('rawlead_api_http', $detail ?: 'API error', ['status' => $code]);

            }

            return new WP_REST_Response(is_array($data) ? $data : [], 200);

        },

    ]);



    register_rest_route('rawlead/v1', '/me/tags', [

        [

            'methods'             => 'GET',

            'permission_callback' => '__return_true',

            'callback'            => static function (WP_REST_Request $request): WP_REST_Response|WP_Error {

                if (rawlead_api_bearer_from_request($request) === '') {

                    return new WP_REST_Response(['tags' => []], 200);

                }

                $url = rawlead_api_base_url() . '/v1/me/tags';

                $response = wp_remote_get($url, [

                    'timeout' => 20,

                    'headers' => rawlead_api_user_headers($request, false),

                ]);

                if (is_wp_error($response)) {

                    return $response;

                }

                $code = (int) wp_remote_retrieve_response_code($response);

                $raw = wp_remote_retrieve_body($response);

                $data = json_decode($raw, true);

                if ($code < 200 || $code >= 300) {

                    $detail = is_array($data) && isset($data['detail']) ? (string) $data['detail'] : $raw;

                    return new WP_Error('rawlead_api_http', $detail ?: 'API error', ['status' => $code]);

                }

                return new WP_REST_Response(is_array($data) ? $data : [], 200);

            },

        ],

        [

            'methods'             => 'PUT',

            'permission_callback' => '__return_true',

            'callback'            => static function (WP_REST_Request $request): WP_REST_Response|WP_Error {

                if (rawlead_api_bearer_from_request($request) === '') {

                    return new WP_Error('rawlead_auth', 'Login required to save skills', ['status' => 401]);

                }

                $tags = $request->get_json_params();

                if (!is_array($tags) || !isset($tags['tags']) || !is_array($tags['tags'])) {

                    return new WP_Error('rawlead_invalid', 'Expected {"tags":[]}', ['status' => 400]);

                }

                $url = rawlead_api_base_url() . '/v1/me/tags';

                $response = wp_remote_request($url, [

                    'method'  => 'PUT',

                    'timeout' => 20,

                    'headers' => array_merge(

                        rawlead_api_user_headers($request, false),

                        ['Content-Type' => 'application/json']

                    ),

                    'body'    => wp_json_encode(['tags' => $tags['tags']]),

                ]);

                if (is_wp_error($response)) {

                    return $response;

                }

                $code = (int) wp_remote_retrieve_response_code($response);

                $raw = wp_remote_retrieve_body($response);

                $data = json_decode($raw, true);

                if ($code < 200 || $code >= 300) {

                    $detail = is_array($data) && isset($data['detail']) ? (string) $data['detail'] : $raw;

                    return new WP_Error('rawlead_api_http', $detail ?: 'API error', ['status' => $code]);

                }

                return new WP_REST_Response(is_array($data) ? $data : [], 200);

            },

        ],

    ]);



    register_rest_route('rawlead/v1', '/me/subscription', [

        [

            'methods'             => 'GET',

            'permission_callback' => '__return_true',

            'callback'            => static function (WP_REST_Request $request): WP_REST_Response|WP_Error {

                if (rawlead_api_bearer_from_request($request) === '') {

                    return new WP_Error('rawlead_auth', 'Login required', ['status' => 401]);

                }

                $url = rawlead_api_base_url() . '/v1/me/subscription';

                $response = wp_remote_get($url, [

                    'timeout' => 20,

                    'headers' => rawlead_api_user_headers($request, false),

                ]);

                if (is_wp_error($response)) {

                    return $response;

                }

                $code = (int) wp_remote_retrieve_response_code($response);

                $raw = wp_remote_retrieve_body($response);

                $data = json_decode($raw, true);

                if ($code < 200 || $code >= 300) {

                    $detail = is_array($data) && isset($data['detail']) ? (string) $data['detail'] : $raw;

                    return new WP_Error('rawlead_api_http', $detail ?: 'API error', ['status' => $code]);

                }

                return new WP_REST_Response(is_array($data) ? $data : [], 200);

            },

        ],

        [

            'methods'             => 'POST',

            'permission_callback' => '__return_true',

            'callback'            => static function (WP_REST_Request $request): WP_REST_Response|WP_Error {

                if (rawlead_api_bearer_from_request($request) === '') {

                    return new WP_Error('rawlead_auth', 'Login required', ['status' => 401]);

                }

                $body = $request->get_json_params();

                if (!is_array($body)) {

                    $body = [];

                }

                $url = rawlead_api_base_url() . '/v1/me/subscription/pause';

                $response = wp_remote_post($url, [

                    'timeout' => 20,

                    'headers' => array_merge(

                        rawlead_api_user_headers($request, false),

                        ['Content-Type' => 'application/json']

                    ),

                    'body'    => wp_json_encode($body),

                ]);

                if (is_wp_error($response)) {

                    return $response;

                }

                $code = (int) wp_remote_retrieve_response_code($response);

                $raw = wp_remote_retrieve_body($response);

                $data = json_decode($raw, true);

                if ($code < 200 || $code >= 300) {

                    $detail = is_array($data) && isset($data['detail']) ? (string) $data['detail'] : $raw;

                    return new WP_Error('rawlead_api_http', $detail ?: 'API error', ['status' => $code]);

                }

                return new WP_REST_Response(is_array($data) ? $data : [], 200);

            },

        ],

    ]);

    register_rest_route('rawlead/v1', '/me/notification-settings', [
        [
            'methods'             => 'GET',
            'permission_callback' => '__return_true',
            'callback'            => static function (WP_REST_Request $request): WP_REST_Response|WP_Error {
                if (rawlead_api_bearer_from_request($request) === '') {
                    return new WP_Error('rawlead_auth', 'Login required', ['status' => 401]);
                }
                $url = rawlead_api_base_url() . '/v1/me/notification-settings';
                $response = wp_remote_get($url, [
                    'timeout' => 20,
                    'headers' => rawlead_api_user_headers($request, false),
                ]);
                if (is_wp_error($response)) {
                    return $response;
                }
                $code = (int) wp_remote_retrieve_response_code($response);
                $raw = wp_remote_retrieve_body($response);
                $data = json_decode($raw, true);
                if ($code < 200 || $code >= 300) {
                    $detail = is_array($data) && isset($data['detail']) ? (string) $data['detail'] : $raw;
                    return new WP_Error('rawlead_api_http', $detail ?: 'API error', ['status' => $code]);
                }
                return new WP_REST_Response(is_array($data) ? $data : [], 200);
            },
        ],
        [
            'methods'             => 'PATCH',
            'permission_callback' => '__return_true',
            'callback'            => static function (WP_REST_Request $request): WP_REST_Response|WP_Error {
                if (rawlead_api_bearer_from_request($request) === '') {
                    return new WP_Error('rawlead_auth', 'Login required', ['status' => 401]);
                }
                $body = $request->get_json_params();
                if (!is_array($body)) {
                    $body = [];
                }
                $url = rawlead_api_base_url() . '/v1/me/notification-settings';
                $response = wp_remote_request($url, [
                    'method'  => 'PATCH',
                    'timeout' => 20,
                    'headers' => array_merge(
                        rawlead_api_user_headers($request, false),
                        ['Content-Type' => 'application/json']
                    ),
                    'body'    => wp_json_encode($body),
                ]);
                if (is_wp_error($response)) {
                    return $response;
                }
                $code = (int) wp_remote_retrieve_response_code($response);
                $raw = wp_remote_retrieve_body($response);
                $data = json_decode($raw, true);
                if ($code < 200 || $code >= 300) {
                    $detail = is_array($data) && isset($data['detail']) ? (string) $data['detail'] : $raw;
                    return new WP_Error('rawlead_api_http', $detail ?: 'API error', ['status' => $code]);
                }
                return new WP_REST_Response(is_array($data) ? $data : [], 200);
            },
        ],
    ]);

    register_rest_route('rawlead/v1', '/support', [
        'methods'             => 'POST',
        'permission_callback' => '__return_true',
        'callback'            => static function (): WP_REST_Response {
            return new WP_REST_Response(['ok' => true], 200);
        },
    ]);

});



add_filter(

    'rest_pre_serve_request',

    static function ($served, $result, $request, $server) {

        if (!($request instanceof WP_REST_Request) || $request->get_route() !== '/rawlead/v1/auth/qr-image') {

            return $served;

        }

        if (!($result instanceof WP_REST_Response)) {

            return $served;

        }

        $data = $result->get_data();

        if (!is_string($data)) {

            return $served;

        }

        status_header($result->get_status());

        foreach ($result->get_headers() as $key => $value) {

            header($key . ': ' . $value);

        }

        echo $data;

        return true;

    },

    10,

    4

);
