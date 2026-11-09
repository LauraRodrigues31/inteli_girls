import React from 'react'
import { Tab, TabList, TabPanel, TabPanels, Tabs } from '@carbon/react'
import type { Region } from '../../types'
import { IndicatorTable } from './IndicatorTable'

interface IndicatorTabsProps {
  region: Region
}

export function IndicatorTabs({ region }: IndicatorTabsProps) {
  return (
    <Tabs>
      <TabList aria-label="Perspectivas da região" contained>
        <Tab>📈 Mercado</Tab>
        <Tab>🫂 Social</Tab>
        <Tab>⚙️ Engenharia</Tab>
        <Tab>💰 Financeiro</Tab>
        <Tab>🤝 Parcerias</Tab>
      </TabList>
      <TabPanels>
        <TabPanel>
          <IndicatorTable data={region.mercado} />
        </TabPanel>
        <TabPanel>
          <IndicatorTable data={region.social} />
        </TabPanel>
        <TabPanel>
          <IndicatorTable data={region.engenharia} />
        </TabPanel>
        <TabPanel>
          <IndicatorTable data={region.financeiro} />
        </TabPanel>
        <TabPanel>
          <IndicatorTable data={region.parcerias} />
        </TabPanel>
      </TabPanels>
    </Tabs>
  )
}
