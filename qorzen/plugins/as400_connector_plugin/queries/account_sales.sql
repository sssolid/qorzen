SELECT
    -- pm.PMPART AS "Number",
    mf.SNSCHR AS "Number",
    mf.SDESCL AS "Description",
    ABS(SUM(pm.PMQTY)) AS "Sold",
    mf.SRET1 AS "Jobber",
    ABS(SUM(pm.PMQTY) * mf.SRET1) AS "Revenue"
    -- SUM(pm.PMQTY * pm.PMCOST) AS "Cost"
FROM
    DSTDATA.INSMFH mf
LEFT JOIN DSTDATA.INPMOVE pm ON
    mf.SPART = pm.PMPART
WHERE
    -- Records only from the beginning of the year
    pm.PMDATE >= '{date}'
    -- Filter out Assembly movements
    AND pm.PMDOC#<> 'ASMBLY'
    -- Only sales
    AND pm.PMTYPE = 'PSL'
    -- From account
    AND pm.PMFRTO = '{account}'
GROUP BY
    mf.SNSCHR, mf.SRET1, mf.SDESCL
ORDER BY
    "Sold" DESC