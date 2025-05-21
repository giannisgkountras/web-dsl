import fs from "fs";
import path from "path";

const prefix = ""; // this is updated after generation

function injectBaseHref(buildDir, publicPathPrefix) {
    const indexPath = path.join(buildDir, "index.html");

    if (!fs.existsSync(indexPath)) {
        console.warn(
            `Warning: index.html not found in ${buildDir}. Cannot inject base href.`
        );
        return;
    }

    let content = fs.readFileSync(indexPath, "utf8");
    const originalContent = content;

    // Ensure publicPathPrefix starts and ends with a slash
    if (!publicPathPrefix.startsWith("/")) {
        publicPathPrefix = "/" + publicPathPrefix;
    }
    if (!publicPathPrefix.endsWith("/")) {
        publicPathPrefix += "/";
    }

    // Inject <base href="...">
    const baseTag = `<base href="${publicPathPrefix}">`;
    const headPattern = /(<head[^>]*>)/i;
    const matchHead = content.match(headPattern);

    if (matchHead) {
        const headTagFull = matchHead[1];
        if (!content.includes(baseTag) && !headTagFull.includes("<base ")) {
            content = content.replace(
                headTagFull,
                `${headTagFull}\n    ${baseTag}`
            );
        }
    } else {
        console.warn(
            `<head> tag not found in ${indexPath}. <base> tag not injected.`
        );
    }

    // Inject window.__BASE_PATH__
    const jsBasePath = publicPathPrefix.replace(/\/$/, ""); // remove trailing slash
    const scriptTagContent = `window.__BASE_PATH__ = "${jsBasePath}";`;
    const scriptTag = `<script>\n      ${scriptTagContent}\n    </script>`;

    if (content.includes(baseTag)) {
        content = content.replace(baseTag, `${baseTag}\n    ${scriptTag}`);
    } else if (matchHead && !content.includes(scriptTagContent)) {
        const headTagFull = matchHead[1];
        content = content.replace(
            headTagFull,
            `${headTagFull}\n    ${scriptTag}`
        );
    } else {
        console.warn(
            `Could not determine where to inject window.__BASE_PATH__ in ${indexPath}.`
        );
    }

    const prefixNoSlash = publicPathPrefix.replace(/\/$/, "");

    // Rewrite src="/..." or href="/..."
    content = content.replace(
        /(src|href)=(["'])(\/[^"'>]+)\2/g,
        (match, attr, quote, url) => {
            if (
                url.startsWith("/") &&
                !url.startsWith(prefixNoSlash + "/") &&
                !/^\/?(data:|mailto:|tel:|\/\/|http:|https:)/.test(url)
            ) {
                return `${attr}=${quote}${prefixNoSlash}${url}${quote}`;
            }
            return match;
        }
    );

    // Rewrite url(/...) in CSS
    content = content.replace(
        /url\((["']?)(\/[^"')]+)\1\)/g,
        (match, quote = "", url) => {
            if (
                url.startsWith("/") &&
                !url.startsWith(prefixNoSlash + "/") &&
                !/^(data:|\/\/|http:|https:)/.test(url)
            ) {
                return `url(${quote}${prefixNoSlash}${url}${quote})`;
            }
            return match;
        }
    );

    if (content === originalContent) {
        console.warn(
            `Warning: Content of ${indexPath} did not change after attempting to inject base href and rewrite paths.`
        );
    } else {
        console.log(`Content of ${indexPath} was modified.`);
    }

    fs.writeFileSync(indexPath, content, "utf8");
    console.log(
        `Processed ${indexPath} with public path prefix '${publicPathPrefix}'`
    );
}

try {
    injectBaseHref("./dist", prefix);
} catch (err) {
    console.error("Error running modify-html.js:", err);
    process.exit(1);
}
